from utilities.transformer import Transformer
from utilities import logger

class DataTabulationClass:

    def __init__(self, class_data, id, parent_product, parent_class = None):
        self.transformer = Transformer(None)
        self.parent_class = parent_class
        self.parent_product = parent_product
        self.id = id
        self.name = self.parent_product.class_name_mappings.get(class_data.get("name"), class_data.get("name"))
        self.label = class_data.get("label")
        self.description = class_data.get('description')
        self.ordinal = str(class_data.get('ordinal'))
        self.parent_class_name = class_data.get("hasParentClass")
        self.variables = []
        self.datasets = []
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        self.validate()
    
    def _build_self_link(self) -> dict:
        name = self.transformer.format_name_for_link(self.name)
        self_link = {
            "href": f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/classes/{name}",
            "title": self.label,
            "type": "Class"
        }
        return self_link
    
    def set_model_link(self, model_href: str):
        name = self.transformer.format_name_for_link(self.name)
        try:
            model_href = model_href + f"/classes/{name}"
            self.parent_product.library_client.get_api_json(model_href)
            model_link = {
                    "href": model_href,
                    "title": self.label,
                    "type": "Class"
                }
            self.links["modelClass"] = model_link
        except:
            pass

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def add_dataset(self, dataset):
        self.datasets.append(dataset)
    
    def set_ordinal(self, ordinal):
        self.ordinal = ordinal

    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "ordinal": self.ordinal
        }

        if self.variables:
            json_data["classVariables"] = [variable.to_json() for variable in self.variables]
        if self.datasets:
            json_data["datasets"] = [dataset.to_json() for dataset in self.datasets]

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Class with name: {self.name} is missing a label. This will cause the title in links to this class to be empty.")
