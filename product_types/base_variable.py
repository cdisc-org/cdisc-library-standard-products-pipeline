from utilities.transformer import Transformer
from utilities import logger
import re
from typing import TypedDict

class BaseVariable:

    PotentialLink = TypedDict("PotentialLink", {"condition": bool, "href": str})

    def __init__(self, parent_product):
        self.transformer = Transformer(None)
        self.parent_product = parent_product
        self.described_value_domain = None
        self.value_list = None
        self.links = {}
        self.name = None
        self.codelist_submission_values = []
    
    def set_prior_version(self) -> dict:
        root_link = self.links.get("rootItem")
        try:
            root_data = self.parent_product.library_client.get_api_json(root_link["href"])
            versions = root_data["_links"]["versions"]
            filtered_versions = [v for v in versions if self.parent_product._get_version_prefix(v["href"].split("/")[3]) == self.parent_product.version_prefix]
            if len(filtered_versions) >= 1:
                sorted_versions = sorted(filtered_versions, key=lambda version: version["href"].split("/")[3])
                for version in reversed(sorted_versions):
                    if self.parent_product._get_version_number(version["href"].split("/")[3]) < self.parent_product.version_number:
                        self.links["priorVersion"] = version
                        return
        except Exception as e:
            logger.error(e)
            logger.error(f"No prior version found for variable: {self.to_string()}")
    
    def set_value_list(self, value_list_string):
        if value_list_string:
            value_list = [code for code in re.split(r'[\n|;|,| or |\\n]', value_list_string)]
            value_list = [value.strip() for value in value_list if len(value) > 0]
            value_list = list(dict.fromkeys(value_list).keys())
            if value_list:
                self.value_list = value_list

    def set_described_value_domain(self, described_value_domain):
        self.described_value_domain = self.parent_product._get_described_value_domain(described_value_domain)

    def add_codelist_links(self, codelist_submission_values: [str]):
        codelists = self.parent_product._get_codelist_links(codelist_submission_values)
        if codelists:
            self.links.setdefault("codelist", []).extend(codelists)
    
    def add_codelist_submission_values(self, values: [str]):
        """
        Converts a string into list of submission values
        """
        self.codelist_submission_values = self.codelist_submission_values + values

    def try_get_api_json(self, link):
        try:
            return self.parent_product.library_client.get_api_json(link)
        except Exception as e:
            None

    def get_variable_variations(self, dataset_name):
        names = [f"{self.name}"]
        if (
            dataset_name
            and type(self.name) == str
            and len(self.name) > 1
            and self.name[:2] == dataset_name
        ):
            names.append(
                self.transformer.replace_str(
                    self.name, dataset_name, "--", 1
                )
            )
        return names

    def to_string(self):
        return self.name
