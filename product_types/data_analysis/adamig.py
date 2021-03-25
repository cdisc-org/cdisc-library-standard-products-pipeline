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
        self.core_map = {
            "adam-adnca": ["NCA Core", "BDS Core", "Core"]
        }
    
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
                "class": self.transformer.cleanup_html_encoding(record["fields"].get("className")),
                "description": self.transformer.cleanup_html_encoding(record["fields"].get("description")),
                "name": self.transformer.cleanup_html_encoding(record["fields"].get("name")),
                "label": self.transformer.cleanup_html_encoding(record["fields"].get("label")),
                "ordinal": str(record["fields"].get("ordinal"))
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
            generated_data = {
                "parentDatastructure": self.transformer.cleanup_html_encoding(record["fields"].get("parentDatastructure", "")),
                "name": self._get_varset_name(record["fields"].get("name")),
                "description": self.transformer.cleanup_html_encoding(record["fields"].get("description")),
                "label": self.transformer.cleanup_html_encoding(record["fields"].get("label")),
                "ordinal": str(record["fields"].get("ordinal")),
                "analysisVariables": []
            }
            generated_data["label"] = f"{generated_data['parentDatastructure']} {record['fields'].get('label')}"
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
            "name": self.transformer.cleanup_html_encoding(variable_data.get("Variable Name")),
            "label": self.transformer.cleanup_html_encoding(variable_data.get("Variable Label")),
            "description": self.transformer.cleanup_html_encoding(variable_data.get("CDISC Notes")),
            "simpleDatatype": self.transformer.cleanup_html_encoding(variable_data.get("Type")),
            "ordinal": self.transformer.cleanup_html_encoding(variable_data.get("Seq. for Order")),
            "datastructure": self.transformer.cleanup_html_encoding(variable_data.get("Class", variable_data.get("Dataset Name")).strip()),
            "codelist": self.transformer.cleanup_html_encoding(variable_data.get("Codelist/Controlled Terms", variable_data.get("Codelist"))),
            "controlledTerms": self.transformer.cleanup_html_encoding(variable_data.get("Controlled Terms", "")),
            "varset": self.transformer.cleanup_html_encoding(variable_data.get("Variable Grouping", "").strip())
        }

        variable["core"] = self._get_variable_core(variable, variable_data)
        if self.product_type != "adamig" and not variable.get("datastructure"):
            variable["datastructure"] = self.product_type.split("-")[-1].upper()
        variable["_links"] = self.__build_variable_links(variable)
        if "codelist" not in variable["_links"]:
            describedValueDomain = self._get_variable_described_value_domain(variable)
            valueList = self._get_variable_value_list(self, variable)
            if describedValueDomain:
                variable["describedValueDomain"] = describedValueDomain
            else:
                # The provided codelist is a value list
                variable["valueList"] = valueList

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
        codelist = variable.get("codelist")
        if self._iscodelist(codelist):
            codelist_links = self._get_codelist_links(codelist)
            if codelist_links:
                links["codelist"] = codelist_links[0]
        return links

    def _build_object_links(self, data: dict, category: str) -> dict:
        links = {}
        name = self.transformer.format_name_for_link(data["name"])
        type_label = "Variable Set" if category == "varsets" else "Data Structure"
        self_link = {}
        if category == "varsets":
            datastructure_name = self.transformer.format_name_for_link(data.get("parentDatastructure", ""))
            self_link["title"] = data.get("label")
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

    def _get_variable_described_value_domain(self, variable: dict) -> str:
        codelist = variable.get("codelist")
        controlled_term = variable.get("controlledTerms")
        if self._isdescribedvaluedomain(controlled_term or codelist):
            return self._get_described_value_domain(controlled_term or codelist)
        else:
            return None
    
    def _get_variable_value_list(self, variable: dict) -> str:
        codelist = variable.get("codelist")
        return [code.strip() for code in re.split(r'[\n|;|\\n|,]', codelist)]

    def _add_variable_to_varset(self, variable: dict, varsets: [dict]):
        varset_name = self._get_varset_name(variable.get("varset"))
        filtered_varsets = [varset for varset in varsets if varset_name == varset.get("name")
                 and variable.get("datastructure") == varset.get('parentDatastructure')]
        if filtered_varsets:
            for varset in filtered_varsets:
                variable["_links"]["parentVariableSet"] = varset["_links"]["self"]
                varset["analysisVariables"] = varset.get("analysisVariables", []) + [variable]
        else:
            logger.error(f"Unable to add variable {variable.get('name')} with datastructure {variable.get('datastructure')} to varset {variable.get('varset')}")

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
        for datastructure in document.get("dataStructures", []):
            self._cleanup_json(datastructure, ["id"])
            for varset in datastructure.get("analysisVariableSets", []):
                self._cleanup_json(varset, ["parentDatastructure"])
                for variable in varset.get("analysisVariables", []):
                    self._cleanup_json(variable, ["datastructure", "codelist", "varset", "controlledTerms"])
        return document

    def _get_variable_core(self, variable, variable_data):
        core_hierarchy = self.core_map.get(self.product_type, ["Core"])
        for core in core_hierarchy:
            if variable_data.get(core):
                return variable_data.get(core)
        return None

    def _get_varset_name(self, name):
        varset_name_mapping = {
            "Period, Subperiod, and Phase Start and End Timing": "PeriodSubperiodStartEndTiming",
            "Record-Level Dose": "RecordLevelDose",
            "Record-Level Treatment and Dose": "RecordLevelTreatmentDose",
            "Suffixes for User-Defined Timing": "SuffixesforUserDefinedTiming",
            "Toxicity and Range": "ToxicityRange"
        }
        varset_name = varset_name_mapping.get(name, name)
        varset_name = varset_name.replace(" ", "").replace("-", "")
        return self.transformer.cleanup_html_encoding(varset_name)
