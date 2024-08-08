from dataclasses import dataclass
from utilities.transformer import Transformer
from utilities import logger
from product_types.base_product import BaseProduct
from product_types.data_tabulation.dataset import Dataset
from product_types.data_tabulation.variable import Variable

@dataclass
class DataTabulationClass:

    transformer: Transformer
    parent_product: BaseProduct
    id: str
    name: str
    label: str
    description: str
    ordinal: str
    parent_class_name: str
    links: dict
    variables: list
    datasets: list

    def __init__(self, class_data = None, id = None, parent_product = None, json_data = None):
        if json_data:
            self._init_from_json(json_data, parent_product)
        else:
            self._init_from_wiki(class_data, id, parent_product)
        self._build_links(parent_product)
        self.validate()

    def _init_from_json(self, json_data, parent_product):
        self.variables = []
        self.transformer = Transformer(None)
        self.id = json_data.get("name")
        self.name = json_data.get("name")
        self.label = json_data.get("label")
        self.description = json_data.get("description")
        self.ordinal = json_data.get("ordinal")
        self.parent_class_name = json_data.get("_links", {}).get("parentClass", {}).get("title")
        [Variable(json_data=variable, parent_product=parent_product, parent_class=self) for variable in json_data.get("classVariables", [])]
        self.datasets = [Dataset(json_data=dataset, parent_product=parent_product, parent_class=self) for dataset in json_data.get("datasets", [])]

    def _init_from_wiki(self, class_data, id, parent_product):
        self.datasets = []
        self.variables = []
        self.transformer = Transformer(None)
        self.parent_product = parent_product
        self.id = id
        self.name = self.parent_product.class_name_mappings.get(class_data.get("name"), class_data.get("name"))
        self.label = class_data.get("label")
        self.description = class_data.get('description')
        self.ordinal = str(class_data.get('ordinal'))
        self.parent_class_name = class_data.get("hasParentClass")

    def _build_links(self, parent_product):
        self.parent_product = parent_product
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        if parent_product.is_ig:
            self.set_model_link()
        prior_version = parent_product._get_prior_version(self.links["self"])
        if prior_version:
            self.add_link("priorVersion", prior_version)

    def _build_self_link(self) -> dict:
        name = self.transformer.format_name_for_link(self.name)
        self_link = {
            "href": f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/classes/{name}",
            "title": self.label,
            "type": "Class"
        }
        return self_link
    
    def merge_from(self, other: 'DataTabulationClass'):
        self.datasets = other.datasets
 
    def set_model_link(self):
        model_href = self.parent_product.summary["_links"]["model"]["href"]
        query = lambda doc: {(clazz["name"]): clazz for clazz in doc["classes"]}
        model_class = self.parent_product.library_client.query_api_json(
            model_href,
            query,
            (self.name),
        )
        if model_class:
            self.links["modelClass"] = model_class["_links"]["self"]

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def add_dataset(self, dataset):
        self.datasets.append(dataset)

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
