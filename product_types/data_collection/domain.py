
from utilities.transformer import Transformer
from utilities import logger

class Domain:

    def __init__(self, domain_data, parent_product, parent_class = None):
        self.transformer = Transformer(None)
        self.parent_class = parent_class
        self.parent_product = parent_product
        self.id = domain_data.get("id")
        self.name = domain_data.get("name")
        self.label = domain_data.get("label")
        self.description = domain_data.get('description')
        self.ordinal = str(domain_data.get('ordinal'))
        self.parent_class_name = domain_data.get('parentClass')
        self.variables = []
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        self.validate()
    
    def _build_self_link(self):
        link_name = self.transformer.remove_str(self.name, " ")
        self_link = {}
        self_link["href"] = f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/domains/{link_name}"
        self_link["title"] = self.label
        self_link["type"] = "CDASH Domain"
        return self_link

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def set_parent_class(self, parent_class):
        self.parent_class = parent_class
        self.add_link("parentClass", parent_class.links.get("self"))
    
    def add_scenario(self, scenario):
        self.links["scenarios"] = self.links.get("scenarios", []) + [scenario.links["self"]]
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "ordinal": self.ordinal
        }

        if self.variables:
            json_data["fields"] = [variable.to_json() for variable in self.variables]

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Domain with name: {self.name} is missing a label. This will cause the title in links to this domain to be empty.")
    
