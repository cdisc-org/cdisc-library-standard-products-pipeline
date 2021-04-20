
from utilities.transformer import Transformer
from utilities import logger
from product_types.base_variable import BaseVariable

class Variable(BaseVariable):

    def __init__(self, variable_data, parent_product, parent_scenario = None, parent_domain = None, parent_class = None):
        super().__init__(parent_product)
        self.product_type = parent_product.product_type
        self.parent_class = parent_class
        self.parent_domain = parent_domain
        self.parent_scenario = parent_scenario
        self.name = variable_data.get(f"{self.product_type.upper()} Variable", "").strip()
        self.label = variable_data.get(f"{self.product_type.upper()} Variable Label")
        self.data_type = variable_data.get("Data Type")
        self.ordinal = str(variable_data.get("Order Number"))
        self.core = variable_data.get("CDASHIG Core")
        self.prompt = self.transformer.cleanup_html_encoding(variable_data.get("Prompt", ""))
        self.question_text = self.transformer.cleanup_html_encoding(variable_data.get("Question Text", ""))
        self.definition = variable_data.get(f"DRAFT {self.product_type.upper()} Definition", "")
        self.implementation_notes = self.transformer.cleanup_html_encoding(variable_data.get("Implementation Notes", ""))
        self.mapping_instructions = self.transformer.cleanup_html_encoding(variable_data.get("Mapping Instructions"))
        self.parent_domain_name = variable_data.get("Domain") if variable_data.get("Domain") != "N/A" else None
        self.parent_class_name = parent_product.class_name_mappings.get(variable_data.get("Observation Class", ""), variable_data.get("Observation Class", ""))
        self.scenario = parent_scenario.name if parent_scenario else None
        self.mapping_targets =  variable_data.get(self.parent_product.tabulation_mapping.upper() + " Target") if \
                 variable_data.get(self.parent_product.tabulation_mapping.upper() + " Target") != "N/A" else None
        self.links = {
            "parentProduct": self.parent_product.summary["_links"]["self"],
            "self": self._build_self_link(),
            "rootItem": self._build_root_link()
        }
        self.codelist = variable_data.get("Controlled Terminology Codelist Name")
        self.described_value_domain = None
        self.value_list = None
        self.validate()
    
    def copy(self):
        new = Variable({}, self.parent_product)
        new.product_type = self.product_type
        new.parent_class = self.parent_class
        new.parent_domain = self.parent_domain
        new.name = self.name
        new.label = self.label
        new.data_type = self.data_type
        new.ordinal = self.ordinal
        new.prompt = self.prompt
        new.question_text = self.question_text
        new.definition = self.definition
        new.implementation_notes = self.implementation_notes
        new.mapping_instructions = self.mapping_instructions
        new.parent_domain_name = self.parent_domain_name
        new.parent_class_name = self.parent_class_name
        new.scenario = self.scenario
        new.mapping_targets =  self.mapping_targets
        new.links = self.links
        new.codelist = self.codelist
        new.described_value_domain = self.described_value_domain
        new.value_list = self.value_list
        new.core = self.core
        return new

    def _build_self_link(self):
        variable_type = self._get_type()
        parent_name = self._get_parent_obj_name()
        variable_name = self.transformer.format_name_for_link(self.name.split("_")[-1])
        return {
                "href": f"/mdr/{self.product_type}/{self.parent_product.version}/{variable_type}/{parent_name}/fields/{variable_name}",
                "title": self.label,
                "type": "Class Variable" if variable_type == "classes" else "Data Collection Field"
            }
    
    def _build_root_link(self):
        variable_type = self._get_type()
        parent_name = self._get_parent_obj_name()
        variable_name = self.transformer.format_name_for_link(self.name.split("_")[-1], [" ", ",","\n", "\\n", '"', "/", "."])
        return {
                "href": f"/mdr/root/{self.product_type}/{variable_type}/{parent_name}/fields/{variable_name}",
                "title": self.label,
                "type": "Root Data Element"
        }
    
    def add_link(self, key, link):
        self.links[key] = link
    
    def set_parent_class(self, parent_class):
        self.parent_class = parent_class
        self.add_link("parentClass", parent_class.links.get("self"))

    def set_parent_domain(self, parent_domain):
        self.parent_domain = parent_domain
        self.add_link("parentDomain", parent_domain.links.get("self"))

    def set_parent_scenario(self, parent_scenario):
        scenario_name = self.transformer.format_name_for_link(parent_scenario.name)
        variable_name = self.name
        self.add_link("parentScenario", parent_scenario.links.get("self"))
        self.links["self"]["href"] = f"/mdr/{self.parent_product.product_type}/{self.parent_product.version}/scenarios/{scenario_name}/fields/{variable_name}" 
        self.links["self"]["type"] = "Data Collection Field"
        self.links["rootItem"]["href"] =  f"/mdr/root/{self.parent_product.product_type}/scenarios/{scenario_name}/fields/{variable_name}"
        self.links["rootItem"]["title"] = f"Version-agnostic anchor element for scenario field {scenario_name}.{variable_name}"
        if "priorVersion" in self.links:
            del self.links["priorVersion"]
        if "implements" in self.links:
            del self.links["implements"]
        self.set_prior_version()
        self.parent_scenario = parent_scenario
    
    def _get_type(self):
        if self.scenario:
            return "scenarios"
        elif self.parent_domain_name:
            return "domains"
        else:
            return "classes"

    def _get_parent_obj_name(self):
        variable_type = self._get_type()
        domain_name = self.transformer.format_name_for_link(self.parent_domain_name)
        if variable_type == "scenarios":
            return f'{domain_name}.{self.transformer.format_name_for_link(self.scenario)}'
        elif variable_type == "domains":
            return domain_name
        else:
            return self.transformer.format_name_for_link(self.parent_class_name)

    def build_mapping_target_links(self):
        targets = [] if not self.mapping_targets else self.mapping_targets.split(";")
        links = []
        category = "datasets" if self.parent_domain_name else "classes"
        parent_dataset = self.parent_product.get_dataset_name(self.parent_domain_name)
        parent_class = self.parent_class_name
        for target in targets:
            target_data = target.split(".")
            target_name = target_data[-1].strip()
            if len(target_data) > 1:
                parent_dataset = self.parent_product.get_dataset_name(target_data[0])
                category = "datasets"
            if target:
                latest_version = self._get_target("datasets", parent_dataset, target_name)
                if latest_version:
                    links.append(latest_version)
                else:
                    latest_version = self._get_target("classes", parent_class, target_name)
                    if latest_version:
                        links.append(latest_version)
                    
                    else:
                        # Fallback to checking for a version of the variable in GeneralObservations before not providing a link
                        latest_version = self._get_target("classes", "GeneralObservations", target_name)
                        if latest_version:
                            links.append(latest_version)
                        else:
                            logger.error(f"Failed to find mapping target for variable: {self.to_string()}")
        if links:
            link = links[0].get("href")
            mapping_key = "MappingTargets"
            if "classes" in link:
                mapping_key = "Class" + mapping_key
            else:
                mapping_key = "Dataset" + mapping_key
            if "sdtmig" in link:
                mapping_key = "sdtmig" + mapping_key
            else:
                mapping_key = "sdtm" + mapping_key
            self.links[mapping_key] = links
    
    def build_implements_link(self):
        name = self.name
        if self.parent_domain_name:
            name = self.transformer.replace_str(name, self.parent_domain_name, "--", 1)
        class_name = self.transformer.format_name_for_link(self.parent_class_name)
        parent_href = self.parent_product.summary["_links"]["parentModel"]["href"] + f"/classes/{class_name}/fields/{name}"
        self.links["implements"] = {
            "href": parent_href,
            "title": self.label,
            "type": "Class Variable"
        }

    def _get_target(self, category: str, parent: str, variable: str) -> dict:
        sdtm_href = f"/mdr/sdtm/{self.parent_product.sdtm_version}/{category}/{parent}/variables/{variable}"
        sdtmig_href = f"/mdr/sdtmig/{self.parent_product.sdtmig_version}/{category}/{parent}/variables/{variable}"
        if not parent:
            return None
        try:
            data = self.parent_product.library_client.get_api_json(sdtm_href)
            return data["_links"]["self"]
        except:
            try:
                data = self.parent_product.library_client.get_api_json(sdtmig_href)
                return data["_links"]["self"]
            except:
                pass
        return None
    
    def to_json(self):
        json_data = {
            "_links": self.links,
            "name": self.name,
            "label": self.label,
            "simpleDatatype": self.data_type,
            "ordinal": self.ordinal,
            "prompt": self.prompt,
            "questionText": self.question_text,
            "implementationNotes": self.implementation_notes,
            "mappingInstructions": self.mapping_instructions,
            "definition": self.definition,
        }

        if self.core:
            json_data["core"] = self.core

        if self.parent_class_name == 'Domain Specific':
            json_data["domainSpecific"] = "true"
        if self.described_value_domain:
            json_data["describedValueDomain"] = self.described_value_domain
        if self.value_list:
            json_data["valueList"] = self.value_list

        return json_data
    
    def validate(self):
        if not self.label:
            logger.info(f"Variable with name: {self.name} is missing a label. This will cause the title in links to this variable to be empty.")
    
    def to_string(self):
        string = f"Name: {self.name}, Parent Class: {self.parent_class_name}, Parent Domain: {self.parent_domain_name}"
        if self.parent_scenario:
            string = string + f", Parent Scenario: {self.parent_scenario.name}"
        return string
