from dataclasses import dataclass
from utilities import logger
from product_types.base_variable import BaseVariable

@dataclass
class Variable(BaseVariable):

    product_type: str
    parent_class: object
    parent_dataset: object
    name_no_prefix: str
    label: str
    data_type: str
    id: str
    ordinal: str
    role: str
    description: str
    core: str
    parent_dataset_name: str
    parent_class_name: str
    codelist: str
    usage_restrictions: str
    variable_ccode: str
    definition: str
    examples: str
    notes: str
    variables_qualified: str
    
    def __init__(self, variable_data = None, parent_product = None, parent_dataset = None, parent_class = None, json_data = None):
        super().__init__(parent_product)
        if json_data:
            self._init_from_json(json_data, parent_dataset, parent_class)
        else:
            self._init_from_wiki(variable_data, parent_product, parent_dataset, parent_class)
        if parent_dataset:
            self.set_parent_dataset(parent_dataset)
            parent_dataset.add_variable(self)
        elif not self.parent_product.is_ig and parent_class:
            self.set_parent_class(parent_class)
            parent_class.add_variable(self)

    def _init_from_json(self, json_data, parent_dataset, parent_class):
        self.name = json_data.get("name")
        self.label = json_data.get("label")
        self.data_type = json_data.get("simpleDatatype")
        self.ordinal = json_data.get("ordinal")
        self.codelist = ""
        self.codelist_submission_values = json_data.get("codelistSubmissionValues")
        self.core = json_data.get("core")
        self.role = json_data.get("role")
        self.description = json_data.get("description")
        self.notes = json_data.get("notes")
        self.definition = json_data.get("definition")
        self.examples = json_data.get("examples")
        self.usage_restrictions = json_data.get("usageRestrictions")
        self.variable_ccode = json_data.get("variableCcode")
        self.described_value_domain = json_data.get("describedValueDomain", "")
        self.value_list = json_data.get("valueList")
        self.id = json_data.get("name")
        self.parent_class_name = parent_class.name
        self.parent_dataset_name = parent_dataset.name
        self._build_links()
        if json_data["_links"].get("codelist"):
            self.add_link("codelist", json_data["_links"].get("codelist"))

    def _init_from_wiki(self, variable_data, parent_product, parent_dataset = None, parent_class = None):
        self.product_type = parent_product.product_type
        self.name = variable_data.get("Variable Name", "").strip()
        self.name_no_prefix = variable_data.get("Variable Name (no prefix)")
        self.label = self.transformer.get_raw_text(variable_data.get("Variable Label"))
        self.data_type = variable_data.get("Type")
        self.id = variable_data.get("id")
        self.ordinal = str(variable_data.get("Seq. for Order", "-1"))
        self.role = variable_data.get("Role")
        self.description = self.transformer.cleanup_html_encoding(variable_data.get("Description", variable_data.get("CDISC Notes", "")))
        self.core = variable_data.get("Core")
        self.parent_dataset_name = parent_dataset.name
        self.parent_class_name = parent_class.name
        self.codelist = variable_data.get("Controlled Terms, Codelist, or Format", variable_data.get("Controlled Terms, Codelist or Format", ""))
        self.described_value_domain = variable_data.get("Format")
        self.usage_restrictions = variable_data.get("Usage Restrictions")
        self.variable_ccode = variable_data.get("Variable C-code")
        self.definition = variable_data.get("Definition")
        self.examples = variable_data.get("Examples")
        self.notes = variable_data.get("Notes")
        self.variables_qualified = variable_data.get("Variable(s) Qualified")
        self.value_list = None
        self.parent_dataset_name = (
            ""
            if self.parent_dataset_name is None
            else self.parent_dataset_name.replace("SDTM ", "").replace(
                "SEND ", ""
            )
        )
        self.parent_class_name = self.parent_class_name.replace("SDTM ", "").replace("SEND ", "")
        self._build_links()

    def _build_links(self):
        self.links ={
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
            "rootItem": self._build_root_link()
        }
        self.set_prior_version()
        if self.parent_product.is_ig:
            try:
                self.build_model_dataset_variable_link()
            except:
                try:
                    self.build_model_class_variable_link()
                except:
                    logger.error(f"No model dataset or class variable found for: {self.parent_dataset_name}.{self.name}")
        self._build_codelist_links()

    def _build_codelist_links(self):
        if self.parent_product._iscodelist(self.codelist) and self.codelist != "N/A":
            codelist_submission_values = self.parent_product.parse_codelist_submission_values(self.codelist)
            self.add_codelist_links(codelist_submission_values)
            self.add_codelist_submission_values(codelist_submission_values)
        elif self.parent_product._isdescribedvaluedomain(self.codelist) and self.codelist != "N/A":
            self.set_described_value_domain(self.codelist)
        elif self.codelist and self.codelist != "N/A":
            # The provided codelist is a value list
            self.set_value_list(self.codelist)

    def _build_self_link(self):
        variable_type = self._get_type()
        parent_name = self._get_parent_obj_name()
        type_label = "SDTM Class Variable" if variable_type == "classes" else "SDTM Dataset Variable"
        variable_name = self.transformer.format_name_for_link(self.name, [" ", ",","\n", "\\n", '"'])
        return  {
            "href": f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/{variable_type}/{parent_name}/variables/{variable_name}",
            "title": self.label,
            "type": type_label
        }
    
    def _build_root_link(self):
        variable_type = self._get_type()
        parent_name = self._get_parent_obj_name()
        type_label = "SDTM Class Variable" if variable_type == "classes" else "SDTM Dataset Variable"
        variable_name = self.transformer.format_name_for_link(self.name, [" ", ",","\n", "\\n", '"'])
        return  {
            "href": f"/mdr/root/{self.parent_product.product_type}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/{variable_type}/{parent_name}/variables/{variable_name}",
            "title": f"Version-agnostic anchor resource for {self.parent_product.product_type.upper().replace('INTEGRATED/', '')}{f' {self.parent_product.product_subtype.upper()}' if  self.parent_product.product_subtype else ''} variable {parent_name}.{variable_name}",
            "type": "Root Data Element"
        }
 
    def get_class_variable(self, class_name: str, variable_name: str) -> dict:
        model_href = self.parent_product.summary["_links"]["model"]["href"]
        query = lambda doc: {
            (clazz["name"], variable["name"]): variable
            for clazz in doc["classes"]
            for variable in clazz.get("classVariables", [])
        }
        model_variable = self.parent_product.library_client.query_api_json(
            model_href,
            query,
            (class_name, variable_name),
        )
        if model_variable:
            return model_variable["_links"]["self"]

    def potential_links(
        self, class_name: str
    ) -> list[BaseVariable.PotentialLink]:
        return [
            {
                "condition": True,
                "class_name": class_name
            },
            {
                "condition": class_name == "Findings About",
                "class_name": "Findings"
            },
            {
                "condition": True,
                "class_name": "General Observations"
            },
        ]
    
    def build_model_class_variable_link(self):
        names = self.get_variable_variations(self.parent_dataset_name)
        data = None
        for name in names:
            for link in self.potential_links(
                self.parent_class_name
            ):
                condition, class_name = link.values()
                if condition:
                    data = self.get_class_variable(class_name, name)
                if data:
                    break
            if data:
                break
        if data:
            self.links["modelClassVariable"] = data
        else:
            raise Exception

    def build_model_dataset_variable_link(self):
        model_href = self.parent_product.summary["_links"]["model"]["href"]
        query = lambda doc: {
            (dataset["name"], variable["name"]): variable
            for dataset in doc["datasets"]
            for variable in dataset.get("datasetVariables", [])
        }
        model_variable = self.parent_product.library_client.query_api_json(
            model_href, query, (self.parent_dataset_name, self.name)
        )
        if model_variable:
            self.links["modelDatasetVariable"] = model_variable["_links"]["self"]
        else:
            raise Exception
    
    def add_link(self, key, link):
        self.links[key] = link
    
    def set_parent_class(self, parent_class):
        self.parent_class = parent_class
        self.add_link("parentClass", parent_class.links.get("self"))

    def set_parent_dataset(self, parent_dataset):
        self.parent_dataset = parent_dataset
        self.add_link("parentDataset", parent_dataset.links.get("self"))

    def _get_type(self):
        if self.parent_dataset_name:
            return "datasets"
        else:
            return "classes"

    def _get_parent_obj_name(self):
        variable_type = self._get_type()
        if variable_type == "datasets":
            return self.parent_dataset_name
        else:
            return self.transformer.format_name_for_link(self.parent_class_name)
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "simpleDatatype": self.data_type,
            "ordinal": self.ordinal,
        }

        if self.codelist_submission_values:
            json_data["codelistSubmissionValues"] = self.codelist_submission_values
        
        if self.core:
            json_data["core"] = self.core
        
        if self.role:
            json_data["role"] = self.role
        if self.description:
            json_data["description"] = self.description
        if self.notes:
            json_data["notes"] = self.notes
        if self.definition:
            json_data["definition"] = self.definition
        if self.examples:
            json_data["examples"] = self.examples
        if self.usage_restrictions:
            json_data["usageRestrictions"] = self.usage_restrictions
        if self.variable_ccode:
            json_data["variableCcode"] = self.variable_ccode
        if self.described_value_domain:
            json_data["describedValueDomain"] = self.described_value_domain
        if self.value_list:
            json_data["valueList"] = self.value_list
        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Variable with name: {self.name} is missing a label. This will cause the title in links to this variable to be empty.")
    
    def to_string(self):
        string = f"Name: {self.name}, Parent Class: {self.parent_class_name}, Parent Dataset: {self.parent_dataset_name}"
        return string
