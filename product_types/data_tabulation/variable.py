
from utilities.transformer import Transformer
from utilities import logger
from product_types.base_variable import BaseVariable

class Variable(BaseVariable):

    def __init__(self, variable_data, parent_product, parent_dataset = None, parent_class = None):
        super().__init__(parent_product)
        self.product_type = parent_product.product_type
        self.parent_class = parent_class
        self.parent_dataset = parent_dataset
        self.name = variable_data.get("Variable Name", "").strip()
        self.name_no_prefix = variable_data.get("Variable Name (no prefix)")
        self.label = self.transformer.get_raw_text(variable_data.get("Variable Label"))
        self.data_type = variable_data.get("Type")
        self.id = variable_data.get("id")
        self.ordinal = str(variable_data.get("Seq. for Order", "-1"))
        self.role = variable_data.get("Role")
        self.description = self.transformer.cleanup_html_encoding(variable_data.get("Description", variable_data.get("CDISC Notes", "")))
        self.core = variable_data.get("Core")
        self.parent_dataset_name = self.parent_product.get_dataset_name(variable_data.get("Dataset Name", ""))
        self.parent_class_name = self.parent_product.class_name_mappings.get(variable_data["Observation Class"], variable_data["Observation Class"])
        self.codelist = variable_data.get("Controlled Terms, Codelist, or Format", variable_data.get("Controlled Terms, Codelist or Format", ""))
        self.described_value_domain = variable_data.get("Format")
        self.usage_restrictions = variable_data.get("Usage Restrictions")
        self.variable_ccode = variable_data.get("Variable C-code")
        self.definition = variable_data.get("Definition")
        self.examples = variable_data.get("Examples")
        self.notes = variable_data.get("Notes")
        self.variables_qualified = variable_data.get("Variable(s) Qualified")
        self.value_list = None
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
            "rootItem": self._build_root_link()
        }

    def _build_self_link(self):
        variable_type = self._get_type()
        parent_name = self._get_parent_obj_name()
        type_label = "SDTM Class Variable" if variable_type == "classes" else "SDTM Dataset Variable"
        variable_name = self.transformer.format_name_for_link(self.name, [" ", ",","\n", "\\n", '"'])
        return  {
            "href": f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}/{variable_type}/{parent_name}/variables/{variable_name}",
            "title": self.label,
            "type": type_label
        }
    
    def _build_root_link(self):
        variable_type = self._get_type()
        parent_name = self._get_parent_obj_name()
        type_label = "SDTM Class Variable" if variable_type == "classes" else "SDTM Dataset Variable"
        variable_name = self.transformer.format_name_for_link(self.name, [" ", ",","\n", "\\n", '"'])
        return  {
            "href": f"/mdr/root/{self.parent_product.product_type}/{variable_type}/{parent_name}/variables/{variable_name}",
            "title": f"Version-agnostic anchor resource for {self.parent_product.product_type.upper()} variable {parent_name}.{variable_name}",
            "type": "Root Data Element"
        }
    
    def build_model_class_variable_link(self):
        model_variable_parent = self.parent_class_name
        parent_model_name = self.transformer.replace_str(str(self.parent_product.parent_model), '.', '-')
        variable_name =  self.name if self.name == self.name_no_prefix else "--" + self.name_no_prefix
        model_link_href = f"/mdr/{self.parent_product.model_type}/{parent_model_name}/classes/{model_variable_parent}/variables/{variable_name}"
        try:
            data = self.parent_product.library_client.get_api_json(model_link_href)
            self.links["modelClassVariable"] = data["_links"]["self"]
        except:
            model_link_href = f"/mdr/{self.parent_product.model_type}/{parent_model_name}/classes/GeneralObservations/variables/{variable_name}"
            data = self.parent_product.library_client.get_api_json(model_link_href)
            self.links["modelClassVariable"] = data["_links"]["self"]

    def build_model_dataset_variable_link(self):
        model_variable_parent = self.parent_dataset_name
        parent_model_name = self.transformer.replace_str(str(self.parent_product.parent_model), '.', '-')
        model_link_href = f"/mdr/{self.parent_product.model_type}/{parent_model_name}/datasets/{model_variable_parent}/variables/{self.name}"
        data = self.parent_product.library_client.get_api_json(model_link_href)
        self.links["modelDatasetVariable"] = data["_links"]["self"]
    
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
