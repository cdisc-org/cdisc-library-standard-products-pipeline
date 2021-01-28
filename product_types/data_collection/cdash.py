from product_types.base_product import BaseProduct
import csv
import sys
from copy import deepcopy
from utilities import logger, constants
import re

class CDASH(BaseProduct):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.product_category = "data-collection"
        self.codelist_types = ["sdtmct"]
        self.tabulation_mapping = "sdtm"
        self.model_type = "cdash"
        self.is_ig = False

    def generate_document(self):
        document = deepcopy(self.summary)
        classes, domains, variables = self.get_metadata()
        document["classes"] = classes
        document["domains"] = domains
        # link variables to appropriate parent structure
        for variable in variables:
            if variable.get("domain"):
                self._add_variable_to_domain(variable, variable.get("domain"), domains)
            if variable.get("class") and variable.get("class") != "Domain Specific" and not self.has_parent_model:
                self._add_variable_to_class(variable, variable.get("class"), classes)
        document = self._cleanup_document(document)
        return document

    def get_metadata(self, parent_href: str = None) -> ([dict], [dict], [dict]):
        self.codelist_mapping = self._get_codelist_mapping()
        classes = self.get_classes()
        domains = self.get_domains()
        variables = self.get_variables()

        return classes, domains, variables

    def validate_document(self, document: dict):
        logger.info("Begin validating")
        for c in document["classes"]:
            self._validate_links(c)
        for d in document["domains"]:
            self._validate_links(d)
        logger.info("Finished validating")
    
    def get_classes(self) -> [dict]:
        document_id = self.config.get(constants.CLASSES)
        classes = []
        expected_fields = set(["name", "label", "description", "ordinal"])
        classes_data = self.wiki_client.get_wiki_table(document_id, constants.CLASSES)
        i = 0
        for record in classes_data["list"]["entry"]:
            i = i+1
            class_data = self._build_object(record, expected_fields)
            class_data["_links"] = self._build_object_links(class_data, "classes")
            classes.append(class_data)
        logger.info(f"Finished loading classes: {i}/{len(classes_data['list']['entry'])}")
        return classes
        

    def get_domains(self) -> [dict]:
        document_id = self.config.get(constants.DOMAINS)
        domains = []
        expected_fields = set(["name", "label", "description", "ordinal", "parentClass"])
        domains_data = self.wiki_client.get_wiki_table(document_id, constants.DOMAINS)
        i = 0
        for record in domains_data["list"]["entry"]:
            i = i+1
            domain_data = self._build_object(record, expected_fields)
            domain_data["_links"] = self._build_object_links(domain_data, "domains")
            domains.append(domain_data)
        logger.info(f"Finished loading domains: {i}/{len(domains_data['list']['entry'])}")
        return domains
    
    def get_variables(self) -> [dict]:
        try:
            document_id = self.config.get(constants.VARIABLES)
        except KeyError:
            document_id = self.wiki_client.update_spec_grabber_content(self.product_type, self.version)
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
    
    def _build_object(self, record: dict, expected_fields: [str], field_mappings: dict = {}) -> dict:
        data = {
            "id": record.get("id")
        }
        for key in record.get("fields", []):
            if key in expected_fields and record["fields"][key] != "N/A":
                data[field_mappings.get(key, key)] = record["fields"][key]
        return data

    def _build_variable(self, variable_data: dict) -> dict:
        variable = {
            "name": variable_data[f"{self.product_type.upper()} Variable"],
            "label": variable_data[f"{self.product_type.upper()} Variable Label"],
            "simpleDatatype": variable_data["Data Type"],
            "ordinal": variable_data["Order Number"],
            "prompt": self.transformer.cleanup_html_encoding(variable_data["Prompt"]),
            "questionText": self.transformer.cleanup_html_encoding(variable_data["Question Text"]),
            "implementationNotes": self.transformer.cleanup_html_encoding(variable_data["Implementation Notes"]),
            "mappingInstructions": self.transformer.cleanup_html_encoding(variable_data["Mapping Instructions"]),
            "definition": variable_data.get(f"DRAFT {self.product_type.upper()} Definition", ""),
            "domain": variable_data.get("Domain") if variable_data.get("Domain") != "N/A" else None,
            "codelist": variable_data["Controlled Terminology Codelist Name"],
            "class": self.class_name_mappings.get(variable_data["Observation Class"], variable_data["Observation Class"]),
            "mappingTargets": variable_data.get(self.tabulation_mapping.upper() + " Target") if \
                 variable_data.get(self.tabulation_mapping.upper() + " Target") != "N/A" else None,
            "scenario": variable_data.get("Data Collection Scenario") if variable_data.get("Data Collection Scenario") != "N/A" else None,
            "implementationOption": variable_data.get("Implementation Options") if variable_data.get("Implementation Options") != "N/A" else None
        }
        variable["_links"] = self.__build_variable_links(variable)
        if variable_data.get("Observation Class") == "Domain Specific":
            variable["domainSpecific"] = True
        return variable

    def __build_variable_links(self, variable: dict) -> dict:
        variable_type = "domains" if variable.get("domain") else "classes"
        mapping_key = "sdtmClassMappingTargets" if variable_type == "classes" else "sdtmigDatasetMappingTargets"
        if variable_type == "domains":
            parent_name = variable.get("domain")
        else:
            parent_name = self.transformer.format_name_for_link(variable.get("class"))
        type_label = "Class Variable" if variable_type == "classes" else "Data Collection Field"
        links = {
            "self": {
                "href": f"/mdr/{self.product_type}/{self.version}/{variable_type}/{parent_name}/fields/{variable['name']}",
                "title": variable["label"],
                "type": type_label
            },
            "rootItem": {
                "href": f"/mdr/root/{self.product_type}/{variable_type}/{parent_name}/fields/{variable['name']}",
                "title": variable["label"],
                "type": "Root Data Element"
            }
        }
        links["parentProduct"] = self.summary["_links"]["self"]
        prior_version = self._get_variable_prior_version(links["rootItem"])
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
        mapping_links = self._build_mapping_links(variable, parent_name)
        if mapping_links:
            links[mapping_key] = mapping_links
        return links

    def _build_object_links(self, data: dict, category: str) -> dict:
        links = {}
        label_map = {
            "classes": "Class",
            "domains": "CDASH Domain",
            "scenarios": "CDASH Scenario"
        }
        name_map = {
            "classes": self.transformer.format_name_for_link(data["name"]),
            "domains": self.transformer.remove_str(data["name"], " "),
            "scenarios": f"{data.get('parentDomain')}.{self.transformer.format_name_for_link(data['name'])}"
        }
        self_link = {}
        self_link["href"] = f"/mdr/{self.product_type}/{self.version}/{category}/{name_map.get(category)}"
        self_link["title"] = data.get("label", data.get("scenario"))
        self_link["type"] = label_map.get(category)
        links["self"] = self_link
        links["parentProduct"] = self.summary["_links"]["self"]
        prior_version = self._get_prior_version(self_link)
        if prior_version:
            links["priorVersion"] = prior_version
        return links
    
    def _add_variable_to_class(self, variable: dict, class_label: str, classes: [dict]):
        filtered_classes = [c for c in classes if c["label"] == class_label]
        if filtered_classes:
            parent = filtered_classes[0]
            variable["_links"]["parentClass"] = parent["_links"]["self"]
            parent["cdashModelFields"] = parent.get("cdashModelFields", []) + [variable]
        else:
            logger.error(f"Unable to add variable {variable['name']} to class {class_label}")

    def _add_variable_to_domain(self, variable: dict, domain_name: str, domains: [dict]):
        filtered_domains = [d for d in domains if d["name"] == domain_name]
        if filtered_domains:
            parent = filtered_domains[0]
            variable["_links"]["parentDomain"] = parent["_links"]["self"]
            parent["fields"] = parent.get("fields", []) + [variable]
        else:
            logger.error(f"Unable to add variable {variable['name']} to domain {domain_name}")

    def _build_mapping_links(self, variable: dict, parent: str) -> [dict]:
        mappingTargets = variable.get("mappingTargets")
        targets = [] if not mappingTargets else mappingTargets.split(";")
        links = []
        category = "datasets" if variable.get("domain") else "classes"
        for target in targets:
            if target:
                target_name = target.split(".")[-1]
                latest_version = self._get_variable_latest_version(category, parent, target_name)
                if latest_version:
                    links.append(latest_version)
                else:
                    # Fallback to checking for a version of the variable in GeneralObservations before not providing a link
                    latest_version = self._get_variable_latest_version(category, "GeneralObservations", target)
                    if latest_version:
                        links.append(latest_version)
        return links
    
    def _get_variable_latest_version(self, category: str, parent: str, variable: str) -> dict:
        root_href = f"/mdr/root/sdtm/{category}/{parent}/variables/{variable}"
        try:
            data = self.library_client.get_api_json(root_href)
            versions = data["_links"]["versions"]
            if versions:
                return versions[-1]
        except:
            pass
        return None
    
    def _get_classes_from_parent(self, parent_link: str) -> [dict]:
        data = self.library_client.get_api_json(parent_link)
        classes = data.get("classes")
        new_classes = []
        for c in classes:
            new_class = {
                "name": c.get("name"),
                "label": c.get("label"),
                "description": c.get("description"),
                "ordinal": c.get("ordinal")
            }
            new_class["_links"] = self._build_object_links(new_class, "classes")
            new_classes.append(new_class)
        logger.info(f"Retrieved {len(new_classes)} classes from parent {parent_link}")
        return new_classes

    def _cleanup_document(self, document: dict) -> dict:
        logger.info("Cleaning generated document")
        for c in document.get("classes", []):
            self._cleanup_json(c, ["id"])
            for field in c.get("cdashModelFields", []):
                self._cleanup_json(field, ["class", "domain", "scenario", "codelist",  "mappingTargets"])
        for domain in document.get("domains", []):
            self._cleanup_json(domain, ["parentClass", "id"])
            for field in domain.get("fields", []):
                self._cleanup_json(field, ["class", "domain", "scenario", "codelist",  "mappingTargets"])
        logger.info("Finished cleaning generated document")
        return document 
    
    def _cleanup_fields(self, fields: [dict]):
        for field in fields:
            self._cleanup_json(field, ["class", "domain", "scenario", "codelist",  "mappingTargets", "implementationOption"])
