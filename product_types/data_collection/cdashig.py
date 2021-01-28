from product_types.data_collection.cdash import CDASH
from product_types.base_product import BaseProduct
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
        classes, domains, variables = self.get_metadata()
        scenarios = self.get_scenarios()
    
        for variable in variables:
            if variable.get("scenario") or variable.get("implementationOption"):
                self._add_variable_to_scenario(variable, scenarios)
            else:
                self._add_variable_to_domain(variable, variable.get("domain"), domains)

        for scenario in scenarios:
            self._add_scenario_to_domain(scenario, domains)
            self._add_scenario_to_class(scenario, classes)

        for domain in domains:
            self._add_domain_to_class(domain, classes)

    
        document["classes"] = classes
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
            scenario_data = {
                "parentClass": record["fields"].get("parentClass"),
                "parentDomain": record["fields"].get("parentDomain"),
                "implementationOption": record["fields"].get("implementationOption", False),
                "ordinal": record["fields"].get("ordinal"),
                "name": record["fields"].get("name")
            }
            if scenario_data.get("implementationOption"):
                name = self.transformer.format_name_for_link(record["fields"].get("name"))
                scenario_data["scenario"] = f"{scenario_data.get('parentDomain')} - Implementation Options: {name}"
            else:
                scenario_data["scenario"] = record["fields"].get("name")
            scenario_data["_links"] = self._build_object_links(scenario_data, "scenarios")
            scenarios.append(scenario_data)
        logger.info(f"Finished loading scenarios: {i}/{len(scenarios_data['list']['entry'])}")
        return scenarios
    
    def get_variables(self) -> [dict]:
        variables = super().get_variables()
        for variable in variables:
            name = variable.get("name", "")
            if variable.get("domain"):
                name = self.transformer.replace_str(name, variable.get('domain'), "--", 1)
            class_name = self.transformer.format_name_for_link(variable.get('class'))
            parent_href = self.summary["_links"]["parentModel"]["href"] + f"/classes/{class_name}/fields/{name}"
            variable["_links"]["implements"] = {
                "href": parent_href,
                "title": variable["label"],
                "type": "Class Variable"
            }
        return variables

    def _add_domain_to_class(self, domain: [dict], classes: [dict]):
        """
        Adds a domain with a known parent class to the parent class' list of domains
        """
        parent_class = domain.get("parentClass")
        filtered_classes = [c for c in classes if c["name"] == parent_class or c.get("id") == parent_class]
        if filtered_classes:
            parent = filtered_classes[0]
            domain["_links"]["parentClass"] = parent["_links"]["self"]
            parent = filtered_classes[0]
            parent["domains"] = parent.get("domains", []) +  [domain]
        else:
            logger.error(f"No parent class found with name: {class_name}")
    
    def _add_variable_to_scenario(self, variable: dict, scenarios: [dict]):
        new_variable = deepcopy(variable)
        parent_scenario = new_variable.get("scenario") if new_variable.get("scenario") else new_variable.get("implementationOption")
        filtered_scenarios = [scenario for scenario in scenarios if parent_scenario == scenario.get("name")]
        if filtered_scenarios:
            for scenario in filtered_scenarios:
                # Modify variable links for scenario use before inserting
                scenario_name = self.transformer.format_name_for_link(scenario.get("name"))
                new_variable["_links"]["parentScenario"] = scenario["_links"]["self"]
                new_variable["_links"]["self"]["href"] = f"/mdr/{self.product_type}/{self.version}/scenarios/{scenario_name}/fields/{variable['name']}" 
                new_variable["_links"]["self"]["type"] = "Data Collection Field"
                new_variable["_links"]["rootItem"]["href"] =  f"/mdr/root/{self.product_type}/scenarios/{scenario_name}/fields/{variable['name']}"
                new_variable["_links"]["rootItem"]["title"] = f"Version-agnostic anchor element for scenario field {scenario_name}.{variable['name']}"
                if new_variable["_links"].get("priorVersion"):
                    del new_variable["_links"]["priorVersion"]
                if new_variable["_links"].get("implements"):
                    del new_variable["_links"]["implements"]
                prior_version = self._get_variable_prior_version(variable["_links"]["rootItem"])
                if prior_version:
                    new_variable["_links"]["priorVersion"] = prior_version
                # Add variable to scenario
                scenario["fields"] = scenario.get("fields", []) + [new_variable]
        else:
            logger.error("Failed attempting to add variable to scenario. " + \
                    f"Variable {new_variable.get('name')} specified scenario {variable.get('scenario')} " + \
                    f"but none found with label {variable.get('scenario')}." )

    def _add_scenario_to_domain(self, scenario: dict, domains: [dict]):
        parent_domain = scenario.get("parentDomain")
        filtered_domains = [domain for domain in domains if parent_domain == domain.get("name") or parent_domain == domain.get("id")]
        if filtered_domains:
            for domain in filtered_domains:
                scenario["_links"]["parentDomain"] = domain["_links"]["self"]
                scenario["domain"] = domain.get("label")
                domain["_links"]["scenarios"] = domain["_links"].get("scenarios", []) + [scenario["_links"]["self"]]
        else:
            logger.error("Failed attempting to add scenario to domain. " + \
                f"Scenario {scenario.get('name')} specified domain {scenario.get('parentDomain')} " + \
                f"but none found with label or id {scenario.get('parentDomain')}." )

    
    def _add_scenario_to_class(self, scenario: dict, classes: [dict]):
        parent_class = scenario.get("parentClass")
        filtered_classes = [c for c in classes if parent_class == c.get("name") or parent_class == c.get("id")]
        if filtered_classes:
            for c in filtered_classes:
                scenario["_links"]["parentClass"] = c["_links"]["self"]
                c["scenarios"] = c.get("scenarios", []) + [scenario]
        else:
            logger.error("Failed attempting to add scenario to domain. " + \
                f"Scenario {scenario.get('name')} specified class {scenario.get('parentClass')} " + \
                f"but none found with label or id {scenario.get('parentClass')}." )

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
        for c in document.get("classes", []):
            self._cleanup_json(c, ["id"])
            for domain in c.get("domains", []):
                self._cleanup_json(domain, ["parentClass", "id"])
                self._cleanup_fields(domain.get("fields", []))
            for scenario in c.get("scenarios", []):
                self._cleanup_json(scenario, ["id", "parentDomain", "parentClass", 'name', 'implementationOption'])
                self._cleanup_fields(scenario.get("fields", []))
        logger.info("Finished cleaning generated document")
        return document
    
    def _cleanup_fields(self, fields: [dict]):
        for field in fields:
            self._cleanup_json(field, ["class", "domain", "scenario", "codelist",  "mappingTargets"])


