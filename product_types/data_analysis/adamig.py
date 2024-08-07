from product_types.data_analysis.adam import ADAM
from product_types.data_analysis.variable import Variable
from product_types.data_analysis.varset import Varset
from product_types.data_analysis.datastructure import Datastructure
import json
from copy import deepcopy
from utilities import logger, constants
import re

class ADAMIG(ADAM):
    def __init__(self, wiki_client, library_client, summary, product_type, version, product_subtype, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, product_subtype, config)
        self.product_category = "data-analysis"
        self.codelist_types = ["adamct", "sdtmct"]
        self.product_type = product_type
        self.version_prefix = "" if product_type.startswith("integrated/") else (product_type + "-")
    
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
                variable_copy = deepcopy(variable)
                parent_varset.add_variable(variable_copy)
            for (sub_class, core) in [
                (sub_class, core)
                for (sub_class, core) in variable.subclass_core.items()
                if core
            ]:
                parent_varset = self._find_subclass_varset(
                    variable.parent_varset_name,
                    variable.parent_datastructure_name,
                    varsets,
                    datastructures,
                    sub_class,
                )
                if parent_varset:
                    variable_copy = deepcopy(variable)
                    variable_copy.core = core
                    parent_varset.add_variable(variable_copy)

        # Assign variable sets to appropriate data structures
        for varset in varsets:
            parent_datastructure = self._find_datastructure(
                varset.parent_datastructure_name, datastructures
            )
            if parent_datastructure:
                varset.set_parent_datastructure(parent_datastructure)
                parent_datastructure.add_varset(varset)
                for variable in varset.variables:
                    variable.set_parent_datastructure(parent_datastructure)
                    variable.set_parent_varset(varset)
        
        # Add parent class links
        self._add_parent_class_datastructure_links(datastructures)

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
                self._validate_links(varset)
                for variable in varset.get("analysisVariables", []):
                    self._validate_links(variable)
        logger.info("Finished validating document")

    def _build_variable(self, variable_data: dict) -> dict:
        variable = Variable(variable_data, self)
        if self._iscodelist(variable.codelist):
            codelist_submission_values = self.parse_codelist_submission_values(variable.codelist)
            codelist_links = self._get_codelist_links(codelist_submission_values)
            if codelist_links:
                variable.add_link("codelist", codelist_links)
            variable.add_codelist_submission_values(codelist_submission_values)
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
                 and varset.parent_datastructure_name == datastructure]
        if filtered_varsets:
            return filtered_varsets[0]
        else:
            logger.error(f"Unable to find varset with name {varset_name} and datastructure {datastructure}")

    def _find_subclass_varset(
        self,
        varset_name: str,
        parent_class: str,
        varsets: [Varset],
        datastructures: [Datastructure],
        sub_class: str,
    ) -> Varset:
        varset_name = self._get_varset_name(varset_name)
        sub_class_short_name = [
            datastructure.name
            for datastructure in datastructures
            if datastructure.sub_class == sub_class
        ][0]
        filtered_varsets = [
            varset
            for varset in varsets
            if varset_name == varset.name
            and varset.parent_datastructure_name == sub_class_short_name
        ]
        if filtered_varsets:
            return filtered_varsets[0]
        filtered_varsets = [
            varset
            for varset in varsets
            if varset_name == varset.name
            and varset.parent_datastructure_name == parent_class
        ]
        if filtered_varsets:
            varset_copy = deepcopy(filtered_varsets[0])
            varset_copy.parent_datastructure_name = sub_class_short_name
            varset_copy.variables = []
            varsets += [varset_copy]
            return varset_copy
        else:
            logger.error(
                f"Unable to find varset with name {varset_name} and datastructure {parent_class}"
            )

    def _find_datastructure(
        self, datastructure_id: str, datastructures: [Datastructure]
    ) -> Datastructure:
        filtered_datastructures = [
            datastructure
            for datastructure in datastructures
            if datastructure_id == datastructure.name
            or datastructure_id == datastructure.id
        ]

        if filtered_datastructures:
            return filtered_datastructures[0]
        else:
            logger.error(
                f"Unable to find datastructure with name or id {datastructure_id}"
            )

    def _find_parent_class_datastructure(
        self, parent_class: str, datastructures: [Datastructure]
    ) -> Datastructure:
        filtered_datastructures = [
            datastructure
            for datastructure in datastructures
            if parent_class == datastructure.parent_class_name
            and not datastructure.sub_class
        ]

        if len(filtered_datastructures) == 1:
            return filtered_datastructures[0]
        else:
            logger.error(
                f"Unable to find single parent class datastructure with class name {parent_class}"
            )

    def _find_parent_class_varset(
        self, varset_name: str, varsets: [Varset]
    ) -> Varset:
        filtered_varsets = [
            varset
            for varset in varsets
            if varset_name == varset.name
        ]

        if len(filtered_varsets) == 1:
            return filtered_varsets[0]
        else:
            logger.error(
                f"Unable to find single parent class varset with varset name {varset_name}"
            )

    def _find_parent_class_variable(
        self, variable_name: str, variables: [Variable]
    ) -> Variable:
        filtered_variables = [
            variable
            for variable in variables
            if variable_name == variable.name
        ]

        if len(filtered_variables) == 1:
            return filtered_variables[0]
        else:
            logger.error(
                f"Unable to find single parent class variable with variable name {variable_name}"
            )

    def _add_parent_class_datastructure_links(self, datastructures: [Datastructure]) -> None:
        for datastructure in datastructures:
            if datastructure.sub_class:
                parent_class_datastructure = self._find_parent_class_datastructure(
                    datastructure.parent_class_name, datastructures
                )
                if parent_class_datastructure:
                    datastructure.add_link(
                        "parentClassDatastructure",
                        deepcopy(parent_class_datastructure.links["self"]),
                    )
                    self._add_parent_class_varset_links(datastructure.varsets, parent_class_datastructure.varsets)

    def _add_parent_class_varset_links(self, varsets: [Varset], parent_class_varsets: [Varset]) -> None:
        for varset in varsets:
            parent_class_varset = self._find_parent_class_varset(
                varset.name, parent_class_varsets
            )
            if parent_class_varset:
                varset.add_link(
                    "parentClassVariableSet",
                    deepcopy(parent_class_varset.links["self"]),
                )
                self._add_parent_class_variable_links(varset.variables, parent_class_varset.variables)
    
    def _add_parent_class_variable_links(self, variables: [Variable], parent_class_variables: [Variable]) -> None:
        for variable in variables:
            parent_class_variable = (
                self._find_parent_class_variable(
                    variable.name, parent_class_variables
                )
            )
            if parent_class_variable:
                variable.add_link(
                    "parentClassVariable",
                    deepcopy(parent_class_variable.links["self"]),
                )

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
