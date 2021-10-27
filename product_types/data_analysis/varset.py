from utilities.transformer import Transformer
from utilities import logger

class Varset:

    def __init__(self, varset_data, parent_product, parent_datastructure = None):
        self.transformer = Transformer(None)
        self.parent_datastructure = parent_datastructure
        self.parent_product = parent_product
        self.id = varset_data.get("id")
        self.parent_datastructure_name = self.transformer.cleanup_html_encoding(varset_data.get("parentDatastructure", ""))
        self.name = self.transformer.cleanup_html_encoding(varset_data.get("name"))
        self.source_label = self.transformer.cleanup_html_encoding(varset_data.get("label"))
        self.description = self.transformer.cleanup_html_encoding(varset_data.get("description"))
        self.ordinal = str(varset_data.get("ordinal"))
        self.variables = []
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
        }
    
    def _build_self_link(self) -> dict:
        name = self.transformer.format_name_for_link(self.name)
        self_link = {}
        datastructure_name = self.transformer.format_name_for_link(self.parent_datastructure_name)
        self_link["title"] = self.label
        version = self.parent_product.version_prefix + self.parent_product.version
        self_link["href"] = f"/mdr/{self.parent_product.model_type}/{version}/datastructures/{datastructure_name}/varsets/{name}"
        self_link["type"] = "Variable Set"
        return self_link

    def add_link(self, key, link):
        self.links[key] = link
    
    def set_parent_datastructure(self, datastructure):
        self.parent_datastructure = datastructure
        self.parent_datastructure_name = self.parent_datastructure.name
        self.label = f'{self.parent_datastructure_name} {self.source_label}'
        self.add_link("parentDatastructure", datastructure.links.get("self"))
        self.add_link("self", self._build_self_link())
        prior_version = self.parent_product._get_prior_version(self.links["self"])
        if prior_version:
            self.add_link("priorVersion", prior_version)
        self.validate()

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "ordinal": self.ordinal,
            "analysisVariables": [variable.to_json() for variable in self.variables]
        }

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Varset with name: {self.name} is missing a label. This will cause the title in links to this varset to be empty.")
    