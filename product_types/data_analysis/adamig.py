from product_types.data_analysis.adam import ADAM
from product_types.data_analysis.variable import Variable
from product_types.data_analysis.varset import Varset
from product_types.data_analysis.datastructure import Datastructure
import json
from copy import deepcopy
from utilities import logger, constants
import re

class ADAMIG(ADAM):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.product_category = "data-analysis"
        self.codelist_types = ["adamct", "sdtmct"]
        self.product_type = product_type
        self.version_prefix = product_type + "-"
    
    def generate_document(self) -> dict:
        if self.has_parent_model:
            self.summary["_links"]["model"] = self._build_model_link()
        document = deepcopy(self.summary)
        
        datastructures = self.get_metadata()
        document["dataStructures"] = [datastructure.to_json() for datastructure in datastructures]
        document = self._cleanup_document(document)
        return document
    
    def get_metadata(self):
        self.codelist_mapping = self._get_codelist_mapping()
        datastructures = self.get_datastructures()
        varsets = self.get_varsets()
        variables = self.get_variables()

        # Assign variables to appropriate variable sets
        for variable in variables:
            if len(datastructures) > 1:
                parent_varset = self._find_varset(variable.parent_varset_name, variable.parent_datastructure_name, varsets)
            else:
                parent_varset = self._find_varset(variable.parent_varset_name, datastructures[0].name, varsets)
            if parent_varset:
                parent_varset.add_variable(variable)

        # Assign variable sets to appropriate data structures
        for varset in varsets:
            parent_datastructures = self._find_datastructures(varset.source_parent_datastructure_name, datastructures)
            for parent_datastructure in parent_datastructures:
                varset_copy = deepcopy(varset)
                varset_copy.set_parent_datastructure(parent_datastructure)
                parent_datastructure.add_varset(varset_copy)
                for variable in varset_copy.variables:
                    variable.set_parent_datastructure(parent_datastructure)
                    variable.set_parent_varset(varset_copy)
        
        return datastructures
    
    def get_datastructures(self) -> [dict]:
        datastructures = []
        document_id = self.config.get(constants.DATASTRUCTURES)
        data = self.wiki_client.get_wiki_table(document_id, constants.DATASTRUCTURES)
        for record in data["list"]["entry"]:
            datastructure = Datastructure(record["fields"], self)
            prior_version = self._get_prior_version(datastructure.links["self"])
            if prior_version:
                datastructure.add_link("priorVersion", prior_version)
            datastructures.append(datastructure)
        for datastructure in datastructures:
            datastructure.add_parent_class_shortname(datastructures)
        logger.info(f"Finished loading {len(datastructures)} datastructures")
        return datastructures
    
    def get_varsets(self) -> [dict]:
        varsets = []
        document_id = self.config.get(constants.VARSETS)
        data = self.wiki_client.get_wiki_table(document_id, constants.VARSETS)
        for record in data["list"]["entry"]:
            varset = Varset(record["fields"], self)
            varsets.append(varset)
        logger.info(f"Finished loading {len(varsets)} Variable sets")
        return varsets
    
    def get_variables(self) -> [dict]:
        try:
            document_id = self.config.get(constants.VARIABLES)
        except KeyError:
            document_id = self.wiki_client.update_spec_grabber_content(self.version_prefix[:-1], self.version)
        variables = []
        json_data = self.wiki_client.get_wiki_json(document_id)
        variables_data = json_data.get("body", {}).get("view", {}).get("value")
        if variables_data:
            reader = self._parse_spec_grabber_output(variables_data)
            for row in reader:
                variable = self._build_variable(row)
                variables.append(variable)
            logger.info(f"Finished loading {len(variables)} variables")
        return variables
    
    def validate_document(self, document: dict):
        logger.info("Begin validating document")
        self._validate_links(document)
        for datastructure in document["dataStructures"]:
            self._validate_links(datastructure)
            for varset in datastructure.get("analysisVariableSet", []):
                self._validate_links(dataset)
                for variable in varset.get("analysisVariables", []):
                    self._validate_links(variable)
        logger.info("Finished validating document")

    def _build_variable(self, variable_data: dict) -> dict:
        variable = Variable(variable_data, self)
        prior_version = self._get_prior_version(variable.links["self"])
        if prior_version:
            variable.add_link("priorVersion", prior_version)
        if self._iscodelist(variable.codelist):
            codelist_links = self._get_codelist_links(variable.codelist)
            if codelist_links:
                variable.add_link("codelist", codelist_links[0])
        else:
            if self._isdescribedvaluedomain(variable.codelist or variable.controlled_terms):
                variable.set_described_value_domain(variable.codelist or variable.controlled_terms)
            else:
                # The provided codelist is a value list
                variable.set_value_list(variable.codelist)
        return variable
    
    def _find_varset(self, varset_name: str, datastructure: str, varsets: [Varset]) -> Varset:
        varset_name = self._get_varset_name(varset_name)
        filtered_varsets = [varset for varset in varsets if varset_name == varset.name
                 and varset.source_parent_datastructure_name == datastructure]
        if filtered_varsets:
            return filtered_varsets[0]
        else:
            logger.error(f"Unable to find varset with name {varset_name} and datastructure {datastructure}")

    def _find_datastructures(self, datastructure_id: str, datastructures: [Datastructure]) -> Datastructure:
        filtered_datastructures = [
            datastructure
            for datastructure in datastructures
            if datastructure_id == datastructure.name
            or datastructure_id == datastructure.id
            or (
                datastructure.sub_class
                and datastructure_id == datastructure.parent_class_shortname
            )
        ]
        
        if filtered_datastructures:
            return filtered_datastructures
        else:
            logger.error(f"Unable to find datastructure with name or id {datastructure_id}")

    def _cleanup_document(self, document: dict) -> dict:
        for datastructure in document.get("dataStructures", []):
            self._cleanup_json(datastructure, ["id"])
            for varset in datastructure.get("analysisVariableSets", []):
                self._cleanup_json(varset, ["parentDatastructure"])
                for variable in varset.get("analysisVariables", []):
                    self._cleanup_json(variable, ["datastructure", "codelist", "varset", "controlledTerms"])
        return document

    def _get_varset_name(self, name):
        return self.transformer.cleanup_html_encoding(name)
