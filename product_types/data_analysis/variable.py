
from utilities.transformer import Transformer
from utilities import logger
from product_types.base_variable import BaseVariable
from re import compile

class Variable(BaseVariable):

    def __init__(self, variable_data, parent_product, parent_datastructure = None, parent_varset = None):
        super().__init__(parent_product)
        self.product_type = parent_product.product_type
        self.parent_varset = parent_varset
        self.parent_datastructure = parent_datastructure
        self.name = self.transformer.cleanup_html_encoding(variable_data.get("Variable Name")).strip()
        self.label = self.transformer.get_raw_text(variable_data.get("Variable Label")).strip()
        self.data_type =self.transformer.cleanup_html_encoding(variable_data.get("Type")).strip()
        self.ordinal = str(self.transformer.cleanup_html_encoding(variable_data.get("Seq. for Order"))).strip()
        self.description = self.transformer.cleanup_html_encoding(variable_data.get("CDISC Notes")).strip()
        self.core = self.transformer.cleanup_html_encoding(variable_data.get("Core")).strip()
        self.parent_datastructure_name = self.transformer.cleanup_html_encoding(variable_data.get("Class", variable_data.get("Dataset Name", "")).strip())
        if self.parent_product.product_type != "adamig" and not self.parent_datastructure_name:
            self.parent_datastructure_name = self.parent_product.product_type.split("-")[-1].upper()
        self.parent_varset_name = variable_data.get("Variable Grouping", "").replace("Variables", "").strip()
        self.codelist = self.transformer.cleanup_html_encoding(variable_data.get("Codelist/Controlled Terms", variable_data.get("Codelist"))).lstrip()
        self.controlled_terms = self.transformer.cleanup_html_encoding(variable_data.get("Controlled Terms", "")).lstrip()
        self.described_value_domain = None
        self.value_list = None
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
        }
        subclass_core_regex = compile("^SubClass (.+) Core$")
        self.subclass_core = {
            subclass_core_regex.match(key).group(
                1
            ): self.transformer.cleanup_html_encoding(value)
            for key, value in variable_data.items()
            if subclass_core_regex.match(key)
        }
        self.validate()

    def _build_self_link(self):
        variable_name = self.transformer.format_name_for_link(self.name, [" ", ",","\n", "\\n", '"', "/", "."])
        datastructure_name = self.transformer.format_name_for_link(self.parent_datastructure_name)
        product_name = self.parent_product.version_prefix + self.parent_product.version
        self_link = {
                "href": f"/mdr/{self.parent_product.product_type if self.parent_product.product_type.startswith('integrated/') else self.parent_product.model_type}/{product_name}{f'/{self.parent_product.product_subtype}' if  self.parent_product.product_subtype else ''}/datastructures/{datastructure_name}/variables/{variable_name}",
                "title": self.label,
                "type": "Analysis Variable"
            }
        return self_link
    
    def set_parent_varset(self, varset):
        self.parent_varset = varset
        self.add_link("parentVariableSet", varset.links.get("self"))
    
    def set_parent_datastructure(self, datastructure):
        self.parent_datastructure = datastructure
        self.parent_datastructure_name = self.parent_datastructure.name
        self.add_link("parentDatastructure", datastructure.links.get("self"))
        self.add_link("self", self._build_self_link())
        prior_version = self.parent_product._get_prior_version(self.links["self"])
        if prior_version:
            self.add_link("priorVersion", prior_version)

    def add_link(self, key, link):
        self.links[key] = link
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "simpleDatatype": self.data_type,
            "core": self.core,
            "ordinal": self.ordinal,
            "description": self.description
        }
        
        if self.codelist_submission_values:
            json_data["codelistSubmissionValues"] = self.codelist_submission_values

        if self.described_value_domain:
            json_data["describedValueDomain"] = self.described_value_domain
        if self.value_list:
            json_data["valueList"] = self.value_list
        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Variable with name: {self.name} is missing a label. This will cause the title in links to this variable to be empty.")

    def to_string(self):
        string = f"Name: {self.name}, Parent Datastructure: {self.parent_datastructure_name}, Parent Varset: {self.parent_varset_name}"
        return string
