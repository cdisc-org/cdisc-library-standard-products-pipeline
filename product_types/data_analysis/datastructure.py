from utilities.transformer import Transformer
from utilities import logger

class Datastructure:

    def __init__(self, datastructure_data, parent_product):
        self.transformer = Transformer(None)
        self.parent_product = parent_product
        self.id = datastructure_data.get("id")
        self.name = self.transformer.cleanup_html_encoding(datastructure_data.get("name"))
        self.label = self.transformer.cleanup_html_encoding(datastructure_data.get("label"))
        self.description = self.transformer.cleanup_html_encoding(datastructure_data.get("description"))
        self.ordinal = str(datastructure_data.get("ordinal"))
        self.sub_class = self.transformer.cleanup_html_encoding(datastructure_data.get("subClass", ""))
        self.parent_class_name = self.transformer.cleanup_html_encoding(datastructure_data.get("className"))
        self.varsets = []
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        self.validate()
    
    def _build_self_link(self) -> dict:
        name = self.transformer.format_name_for_link(self.name)
        self_link = {}
        self_link["title"] = self.label
        version = self.parent_product.version_prefix + self.parent_product.version
        self_link["href"] = f"/mdr/{self.parent_product.model_type}/{version}/datastructures/{name}"
        self_link["type"] = "Data Structure"
        return self_link

    def add_link(self, key, link):
        self.links[key] = link
    
    def add_varset(self, varset):
        self.varsets.append(varset)
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "class": self.parent_class_name,
            "description": self.description,
            "name": self.name,
            "label": self.label,
            "ordinal": self.ordinal
        }

        if self.sub_class:
            json_data["subClass"] = self.sub_class

        if self.varsets:
            json_data["analysisVariableSets"] = [varset.to_json() for varset in self.varsets]

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Datastructure with name: {self.name} is missing a label. This will cause the title in links to this datastructure to be empty.")
