from product_types.data_collection.cdash import CDASH
from product_types.base_product import BaseProduct
from product_types.data_collection.variable import Variable
from product_types.data_collection.domain import Domain
from product_types.data_collection.data_collection_class import DataCollectionClass
from product_types.data_collection.scenario import Scenario
from copy import deepcopy
from utilities import logger, constants

class CDASHIG(CDASH):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.model_type = "cdash"
        self.tabulation_mapping = "sdtmig"
        self.is_ig = True

    def generate_document(self) -> dict:
        if self.has_parent_model:
            self.summary["_links"]["parentModel"] = self._build_model_link()
        document = deepcopy(self.summary)
        parent_href = self.summary["_links"]["parentModel"]["href"]
        scenarios = self.get_scenarios()
        classes, domains, variables = self.get_metadata(scenarios)
    
        for variable in variables:
            parent_domain = self._find_domain(variable.parent_domain_name, domains)
            if variable.parent_scenario:
                new_variable = variable.copy()
                new_variable.set_parent_scenario(variable.parent_scenario)
                variable.parent_scenario.add_variable(new_variable)
            elif parent_domain:
                variable.set_parent_domain(parent_domain)
                parent_domain.add_variable(variable)

        for scenario in scenarios:
            parent_domain = self._find_domain(scenario.parent_domain_name, domains)
            parent_class = self._find_class(scenario.parent_class_name, classes)

            if parent_domain:
                scenario.set_parent_domain(parent_domain) 
                parent_domain.add_scenario(scenario)
            if parent_class:
                scenario.set_parent_class(parent_class)
                parent_class.add_scenario(scenario)

        for domain in domains:
            parent_class = self._find_class(domain.parent_class_name, classes)
            if parent_class:
                domain.set_parent_class(parent_class)
                parent_class.add_domain(domain)

    
        document["classes"] = [c.to_json() for c in classes]
        document = self._cleanup_document(document)
        return document
    
    def get_scenarios(self):
        document_id = self.config.get(constants.SCENARIOS)
        scenarios = []
        expected_fields = set(["name", "ordinal", "parentClass", "parentDomain", "implementationOption"])
        scenarios_data = self.wiki_client.get_wiki_table(document_id, constants.SCENARIOS)
        i = 0
        for record in scenarios_data["list"]["entry"]:
            i = i+1
            scenario = Scenario(record["fields"], self)
            prior_version = self._get_prior_version(scenario.links["self"])
            if prior_version:
                scenario.add_link("priorVersion", prior_version)
            scenarios.append(scenario)
        logger.info(f"Finished loading scenarios: {i}/{len(scenarios_data['list']['entry'])}")
        return scenarios
    
    def get_variables(self, scenarios = []) -> [dict]:
        variables = super().get_variables(scenarios)
        for variable in variables:
            variable.build_implements_link()
        return variables

    def validate_document(self, document: dict):
        logger.info("Begin validating")
        for c in document["classes"]:
            self._validate_links(c)
            for d in c.get("domains", []):
                self._validate_links(d)
                for field in d.get("fields", []):
                    self._validate_links(field)
            for scenario in c.get("scenarios", []):
                self._validate_links(scenario)
                for field in scenario.get("fields", []):
                    self._validate_links(field)
        logger.info("Finished validating")
    
    def _cleanup_document(self, document: dict) -> dict:
        logger.info("Cleaning generated document")
        self._cleanup_json(document, ["sdtmigVersion"])
        for c in document.get("classes", []):
            self._cleanup_json(c, ["id"])
            for domain in c.get("domains", []):
                self._cleanup_json(domain, ["parentClass", "id"])
                self._cleanup_fields(domain.get("fields", []))
            for scenario in c.get("scenarios", []):
                self._cleanup_json(scenario, ["id", "parentDomain", "parentClass", 'name', "label", 'implementationOption'])
                self._cleanup_fields(scenario.get("fields", []))
        logger.info("Finished cleaning generated document")
        return document
    
    def _cleanup_fields(self, fields: [dict]):
        for field in fields:
            self._cleanup_json(field, ["class", "domain", "scenario", "codelist",  "mappingTargets"])


