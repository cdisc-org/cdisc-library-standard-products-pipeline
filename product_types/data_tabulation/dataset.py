from utilities.transformer import Transformer
from utilities import logger

class Dataset:

    def __init__(self, dataset_data, id, parent_product, parent_class = None):
        self.transformer = Transformer(None)
        self.parent_class = parent_class
        self.parent_product = parent_product
        self.id = id
        self.name = self.parent_product.get_dataset_name(dataset_data.get("name", ""))
        self.label = dataset_data.get("label")
        self.description = dataset_data.get('description')
        self.ordinal = str(dataset_data.get('ordinal'))
        self.parent_class_name = dataset_data.get("hasParentContext")
        self.structure = dataset_data.get("datasetStructure")
        self.status = dataset_data.get("publicationStatus", "Final")
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
            "href": f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}/datasets/{name}",
            "title": self.label,
            "type": "SDTM Dataset"
        }
        return self_link
    
    def set_model_link(self, model_href: str):
        name = self.transformer.format_name_for_link(self.name)
        try:
            model_href = model_href + f"/datasets/{name}"
            self.parent_product.library_client.get_api_json(model_href)
            model_link = {
                    "href": model_href,
                    "title": self.label,
                    "type": "SDTM Dataset"
                }
            self.links["modelDataset"] = model_link
        except:
            pass

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def set_parent_class(self, parent_class):
        self.parent_class = parent_class
        self.add_link("parentClass", parent_class.links.get("self"))
    
    def set_ordinal(self, ordinal):
        self.ordinal = ordinal

    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "status": self.status,
            **({} if self.description is None else {"description": self.description}),
            "ordinal": self.ordinal,
            **({} if self.structure is None else {"datasetStructure": self.structure}),
        }

        if self.variables:
            json_data["datasetVariables"] = [variable.to_json() for variable in self.variables]

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Dataset with name: {self.name} is missing a label. This will cause the title in links to this dataset to be empty.")

