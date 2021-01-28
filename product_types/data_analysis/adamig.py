from product_types.data_analysis.adam import ADAM
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
        
        datastructures, varsets, variables = self.get_metadata()
        document["dataStructures"] = datastructures
        document = self._cleanup_document(document)
        return document
    
    def get_metadata(self):
        self.codelist_mapping = self._get_codelist_mapping()
        datastructures = self.get_datastructures()
        varsets = self.get_varsets()
        variables = self.get_variables()

        # Assign variables to appropriate variable sets
        for variable in variables:
            self._add_variable_to_varset(variable, varsets)

        # Assign variable sets to appropriate data structures
        for varset in varsets:
            self._add_varset_to_datastructure(varset, datastructures)
        
        return datastructures, varsets, variables
    
    def get_datastructures(self) -> [dict]:
        datastructures = []
        document_id = self.config.get(constants.DATASTRUCTURES)
        expected_fields = set(["name", "label", "description", "ordinal", "className"])
        field_names_mapping = {
            "className": "class"
        }
        data = self.wiki_client.get_wiki_table(document_id, constants.DATASTRUCTURES)
        for record in data["list"]["entry"]:
            generated_data = {
                "class": record["fields"].get("className"),
                "description": record["fields"].get("description"),
                "name": record["fields"].get("name"),
                "label": record["fields"].get("label"),
                "ordinal": record["fields"].get("ordinal")
            }
            generated_data["_links"] = self._build_object_links(generated_data, "datastructures")
            datastructures.append(generated_data)
        logger.info("Finished loading datastructures")
        return datastructures
    
    def get_varsets(self) -> [dict]:
        varsets = []
        document_id = self.config.get(constants.VARSETS)
        expected_keys = set(["name", "label", "description", "ordinal", "parentDatastructure"])
        data = self.wiki_client.get_wiki_table(document_id, constants.VARSETS)
        for record in data["list"]["entry"]:
            generated_data = {}
            for key in record["fields"]:
                if key in expected_keys:
                    generated_data[key] = record["fields"][key]
            generated_data["_links"] = self._build_object_links(generated_data, "varsets")
            varsets.append(generated_data)
        logger.info("Finished loading Variable sets")
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
            logger.info("Finished loading variables")
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
        variable = {
            "name": variable_data.get("Variable Name"),
            "label": variable_data.get("Variable Label"),
            "description": self.transformer.cleanup_html_encoding(variable_data.get("CDISC Notes")),
            "core": variable_data.get("Core"),
            "simpleDatatype": variable_data.get("Type"),
            "ordinal": 1,
            "datastructure": variable_data.get("Dataset Name", variable_data.get("Class")).strip(),
            "codelist": variable_data.get("Codelist/Controlled Terms"),
            "varset": variable_data.get("Variable Grouping", "").strip()
        }
        variable["_links"] = self.__build_variable_links(variable)
        return variable

    def __build_variable_links(self, variable: dict) -> dict:
        variable_name = self.transformer.format_name_for_link(variable['name'])
        self_link = {
                "href": f"/mdr/{self.model_type}/{self.version_prefix + self.version}/datastructures/{variable.get('datastructure')}/variables/{variable_name}",
                "title": variable["label"],
                "type": "Analysis Variable"
            }
        links = {
            "self": self_link
        }
        links["parentProduct"] = self.summary["_links"]["self"]
        prior_version = self._get_prior_version(self_link)
        if prior_version:
            links["priorVersion"] = prior_version
        codelist = variable.get("codelist", "")
        if self._iscodelist(codelist):
            links["codelist"] = self._get_codelist_links(codelist)
        elif self._isdescribedvaluedomain(codelist):
            variable["describedValueDomain"] = self._get_described_value_domain(codelist)
        elif codelist:
            # The provided codelist is a value list
            variable["valueList"] = [code for code in re.split(r'[\n|;|\\n|,]', codelist)]
        return links

    def _build_object_links(self, data: dict, category: str) -> dict:
        links = {}
        name = self.transformer.format_name_for_link(data["name"])
        type_label = "Variable Set" if category == "varsets" else "Data Structure"
        self_link = {}
        if category == "varsets":
            datastructure_name = self.transformer.format_name_for_link(data.get("parentDatastructure", ""))
            self_link["href"] = f"/mdr/{self.model_type}/{self.version_prefix+self.version}/datastructures/{datastructure_name}/varsets/{name}"
        else:
            self_link["href"] = f"/mdr/{self.model_type}/{self.version_prefix+self.version}/{category}/{name}"
            self_link["title"] = data.get("label")
        self_link["type"] = type_label
        links["self"] = self_link
        links["parentProduct"] = self.summary["_links"]["self"]
        prior_version = self._get_prior_version(self_link)
        if prior_version:
            links["priorVersion"] = prior_version
        return links
    
    def _add_variable_to_varset(self, variable: dict, varsets: [dict]):
        filtered_varsets = [varset for varset in varsets if variable.get("varset") == varset.get("name")
                 and variable.get("datastructure") == varset.get('parentDatastructure')]
        if filtered_varsets:
            for varset in filtered_varsets:
                variable["_links"]["parentVariableSet"] = varset["_links"]["self"]
                varset["analysisVariables"] = varset.get("analysisVariables", []) + [variable]

    def _add_varset_to_datastructure(self, varset: dict, datastructures: [dict]):
        parent_datastructure = varset.get("parentDatastructure")
        filtered_datastructures = [datastructure for datastructure in datastructures if parent_datastructure == datastructure.get("name") \
            or parent_datastructure == datastructure.get("id")]
        
        for datastructure in filtered_datastructures:
            varset["_links"]["parentDatastructure"] = datastructure["_links"]["self"]
            for variable in varset.get("analysisVariables", []):
                variable["_links"]["parentDatastructure"] = datastructure["_links"]["self"]
            datastructure["analysisVariableSets"] = datastructure.get("analysisVariableSets", []) + [varset]
    
    def _cleanup_document(self, document: dict) -> dict:
        for datastructure in document.get("datastructures", []):
            self._cleanup_json(datastructure, ["id"])
            for varset in datastructure.get("analysisVariableSets", []):
                self._cleanup_json(varset, ["parentDatastructure"])
                for variable in varset.get("analysisVariables", []):
                    self._cleanup_json(variable, ["datastructure", "codelist", "varset"])
        return document
