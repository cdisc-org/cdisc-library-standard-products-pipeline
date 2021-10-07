from product_types.base_product import BaseProduct
from product_types.data_collection.variable import Variable
from product_types.data_collection.domain import Domain
from product_types.data_collection.data_collection_class import DataCollectionClass
import csv
import sys
from copy import deepcopy
from utilities import logger, constants
import re

class CDASH(BaseProduct):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.product_category = "data-collection"
        self.codelist_types = ["sdtmct", "cdashct"]
        self.model_type = "cdash"
        self.tabulation_mapping = "sdtm"
        self.sdtm_version = summary.get("sdtmVersion")
        self.sdtmig_version = summary.get("sdtmigVersion")
        self.is_ig = False

    def generate_document(self):
        document = deepcopy(self.summary)
        classes, domains, variables = self.get_metadata()

        for domain in domains:
            parent_class = self._find_class(domain.parent_class_name, classes)
            if parent_class:
                domain.set_parent_class(parent_class)
        # link variables to appropriate parent structure
        for variable in variables:
            parent_class = self._find_class_by_label(variable.parent_class_name, classes)
            parent_domain = self._find_domain(variable.parent_domain_name, domains)
            if parent_class:
                variable.set_parent_class(parent_class)
            if parent_domain:
                variable.set_parent_domain(parent_domain)
                parent_domain.add_variable(variable)
            elif parent_class:
                parent_class.add_variable(variable)

        document["classes"] = [class_obj.to_json() for class_obj in classes]
        document["domains"] = [domain.to_json() for domain in domains]
        self._cleanup_document(document)
        return document

    def get_metadata(self, scenarios = []) -> ([dict], [dict], [dict]):
        self.codelist_mapping = self._get_codelist_mapping()
        classes = self.get_classes()
        domains = self.get_domains()
        variables = self.get_variables(scenarios)

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
        classes_data = self.wiki_client.get_wiki_table(document_id, constants.CLASSES)
        i = 0
        for record in classes_data["list"]["entry"]:
            i = i+1
            class_obj = DataCollectionClass(record["fields"], self)
            prior_version = self._get_prior_version(class_obj.links["self"])
            if prior_version:
                class_obj.add_link("priorVersion", prior_version)
            if self.is_ig:
                class_obj.set_model_link(self.summary["_links"]["model"]["href"])
            classes.append(class_obj)
        logger.info(f"Finished loading classes: {i}/{len(classes_data['list']['entry'])}")
        return classes
        

    def get_domains(self) -> [dict]:
        document_id = self.config.get(constants.DOMAINS)
        domains = []
        domains_data = self.wiki_client.get_wiki_table(document_id, constants.DOMAINS)
        i = 0
        for record in domains_data["list"]["entry"]:
            i = i+1
            domain = Domain(record["fields"], self)
            prior_version = self._get_prior_version(domain.links["self"])
            if prior_version:
                domain.add_link("priorVersion", prior_version)
            domains.append(domain)
        logger.info(f"Finished loading domains: {i}/{len(domains_data['list']['entry'])}")
        return domains
    
    def get_variables(self, scenarios = []) -> [dict]:
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
                parent_scenario = self._find_scenario(row, scenarios)
                variable = Variable(row, self, parent_scenario=parent_scenario)
                if self._iscodelist(variable.codelist) and variable.codelist != "N/A":
                    variable.add_codelist_links(variable.codelist)
                elif self._isdescribedvaluedomain(variable.codelist) and variable.codelist != "N/A":
                    variable.set_described_value_domain(variable.codelist)
                elif variable.codelist and variable.codelist != "N/A":
                    # The provided codelist is a value list
                    variable.set_value_list(variable.codelist)
                if variable.subset_codelist != "N/A":
                    variable.add_codelist_links(variable.subset_codelist)
                variable.build_mapping_target_links()
                variable.set_prior_version()
                variable.validate()
                variables.append(variable)
            logger.info("Finished loading variables")
        return variables
    
    def _find_scenario(self, variable_data, scenarios):
        implementation_option = variable_data.get("Implementation Options") if variable_data.get("Implementation Options") != "N/A" else None
        scenario_name = implementation_option or variable_data.get("Data Collection Scenario")
        class_name = self.class_name_mappings.get(variable_data["Observation Class"], variable_data["Observation Class"])
        domain_name = variable_data.get("Domain")
        if not scenario_name or scenario_name == "N/A":
            return None
        filtered_scenarios = [s for s in scenarios if s.label == scenario_name and s.parent_class_name == class_name and s.parent_domain_name == domain_name]
        if filtered_scenarios:
            return filtered_scenarios[0]
        else:
            logger.error(f"No scenarios found with name {scenario_name} and class {class_name} and domain name {domain_name}" )
            return None

    def _find_domain(self, domain_name: str, domains):
        if not domain_name:
            return None
        filtered_domains = [d for d in domains if d.name == domain_name]
        if filtered_domains:
            return filtered_domains[0]
        else:
            return None

    def _find_class(self, class_id: str, classes):
        """
        Finds a class from the list of classes. Class_id can be a name or an id referencing a class
        """
        filtered_classes = [c for c in classes if c.name == class_id or c.id == class_id]
        if filtered_classes:
            return filtered_classes[0]
        else:
            logger.error(f"No parent class found with name: {class_id}")
            return None
    
    def _find_class_by_label(self, class_label: str, classes):
        """
        Finds a class from the list of classes.
        """
        if class_label == "Domain Specific":
            return None
        filtered_classes = [c for c in classes if c.label == class_label]
        if filtered_classes:
            return filtered_classes[0]
        else:
            logger.error(f"No parent class found with label: {class_label}")
            return None

    def _cleanup_document(self, document: dict) -> dict:
        logger.info("Cleaning generated document")
        self._cleanup_json(document, ["sdtmVersion", "sdtmigVersion"])
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
