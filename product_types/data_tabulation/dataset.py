from dataclasses import dataclass
from utilities.transformer import Transformer
from utilities import logger
from product_types.base_product import BaseProduct
from product_types.data_tabulation.variable import Variable


@dataclass
class Dataset:

    transformer: Transformer
    parent_product: BaseProduct
    id: str
    name: str
    label: str
    description: str
    ordinal: str
    parent_class_name: str
    structure: str
    status: str
    links: dict
    parent_class: object
    variables: list

    def __init__(self, dataset_data = None, id = None, parent_product = None, json_data = None, parent_class = None):
        if json_data:
            self._init_from_json(json_data, parent_product, parent_class)
        else:
            self._init_from_wiki(dataset_data, id, parent_product)
        self.validate()

    def _init_from_json(self, json_data, parent_product, parent_class):
        self.variables = []
        self.parent_class = parent_class
        self.transformer = Transformer(None)
        self.id = json_data.get("name")
        self.name = json_data.get("name")
        self.label = json_data.get("label")
        self.description = json_data.get("description")
        self.ordinal = json_data.get("ordinal")
        self.parent_class_name = parent_class.name
        self.structure = json_data.get("datasetStructure")
        self.status = json_data.get("status")
        self._build_links(parent_product)
        [Variable(json_data=variable, parent_product=parent_product, parent_class=parent_class, parent_dataset=self) for variable in json_data.get("datasetVariables", [])]
 
    def _init_from_wiki(self, dataset_data, id, parent_product):
        self.variables = []
        self.parent_class = None
        self.transformer = Transformer(None)
        self.id = id
        self.name = parent_product.get_dataset_name(dataset_data.get("name", ""))
        self.label = dataset_data.get("label")
        self.description = dataset_data.get('description')
        self.ordinal = str(dataset_data.get('ordinal'))
        self.parent_class_name = dataset_data.get("hasParentContext")
        self.structure = dataset_data.get("datasetStructure")
        self.status = dataset_data.get("publicationStatus", "Final")
        self._build_links(parent_product)

    def _build_links(self, parent_product):
        self.parent_product = parent_product
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
        }
        if self.parent_product.is_ig:
            self.set_model_link()
        prior_version = self.parent_product._get_prior_version(self.links["self"])
        if prior_version:
            self.add_link("priorVersion", prior_version)
    
    def _build_self_link(self) -> dict:
        name = self.transformer.format_name_for_link(self.name)
        self_link = {
            "href": f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/datasets/{name}",
            "title": self.label,
            "type": "SDTM Dataset"
        }
        return self_link
    
    def merge_from(self, other: 'Dataset'):
        if not self.variables:
            self.variables = other.variables

    def set_model_link(self):
        model_href = self.parent_product.summary["_links"]["model"]["href"]
        query = lambda doc: {(dataset["name"]): dataset for dataset in doc["datasets"]}
        model_dataset = self.parent_product.library_client.query_api_json(
            model_href,
            query,
            (self.name),
        )
        if model_dataset:
            self.links["modelDataset"] = model_dataset["_links"]["self"]

    def add_link(self, key, link):
        self.links[key] = link

    def add_variable(self, variable):
        self.variables.append(variable)
    
    def set_parent_class(self, parent_class):
        self.parent_class = parent_class
        self.add_link("parentClass", parent_class.links.get("self"))

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
