from utilities.transformer import Transformer
from utilities import logger

class Scenario:

    def __init__(self, scenario_data, parent_product, parent_class = None, parent_domain=None):
        self.transformer = Transformer(None)
        self.parent_class = parent_class
        self.parent_product = parent_product
        self.id = scenario_data.get("id")
        self.name = scenario_data.get("name")
        self.label = scenario_data.get("label")
        self.domain_label = None
        self.parent_domain_name = scenario_data.get('parentDomain')
        self.parent_class_name = scenario_data.get('parentClass')
        self.implementation_option = scenario_data.get('implementationOption', False)
        self.ordinal = str(scenario_data.get('ordinal'))
        self.variables = []
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        if self.implementation_option:
            name = self.transformer.format_name_for_link(scenario_data.get("name", ""))
            self.scenario = f"{self.parent_domain_name} - Implementation Options: {self.name}"
        else:
            self.scenario = self.label
        self.validate()
    
    def _build_self_link(self):
        parent_domain_name = self.transformer.format_name_for_link(self.parent_domain_name)
        link_name = f"{parent_domain_name}.{self.transformer.format_name_for_link(self.name)}"
        self_link = {}
        self_link["href"] = f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}/scenarios/{link_name}"
        self_link["title"] = self.label
        self_link["type"] = "CDASH Scenario"
        return self_link

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def set_parent_class(self, parent_class):
        self.parent_class = parent_class
        self.add_link("parentClass", parent_class.links.get("self"))

    def set_parent_domain(self, parent_domain):
        self.parent_domain = parent_domain
        self.domain_label = parent_domain.label
        self.add_link("parentDomain", parent_domain.links.get("self"))

    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "ordinal": self.ordinal,
            "domain": self.domain_label,
            "domainName": self.parent_domain_name,
            "scenario": self.scenario
        }

        if self.variables:
            json_data["fields"] = [variable.to_json() for variable in self.variables]

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Scenario with name: {self.name} is missing a label. This will cause the title in links to this scenario to be empty.")