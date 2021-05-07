from utilities.transformer import Transformer
from utilities import logger

class DataCollectionClass:

    def __init__(self, class_data, parent_product, parent_class = None):
        self.transformer = Transformer(None)
        self.parent_class = parent_class
        self.parent_product = parent_product
        self.id = class_data.get("id")
        self.name = class_data.get("name")
        self.label = class_data.get("label")
        self.description = class_data.get('description')
        self.ordinal = str(class_data.get('ordinal'))
        self.variables = []
        self.domains = []
        self.scenarios = []
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        self.validate()
    
    def _build_self_link(self):
        link_name = self.transformer.format_name_for_link(self.name)
        self_link = {}
        self_link["href"] = f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}/classes/{link_name}"
        self_link["title"] = self.label
        self_link["type"] = "Class"
        return self_link

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def add_domain(self, domain):
        self.domains.append(domain)
    
    def add_scenario(self, scenario):
        self.scenarios.append(scenario)
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "ordinal": self.ordinal
        }

        if self.variables:
            json_data["cdashModelFields"] = [variable.to_json() for variable in self.variables]
        if self.domains:
            json_data["domains"] = [domain.to_json() for domain in self.domains]
        if self.scenarios:
            json_data["scenarios"] = [scenario.to_json() for scenario in self.scenarios]

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Class with name: {self.name} is missing a label. This will cause the title in links to this class to be empty.")
    