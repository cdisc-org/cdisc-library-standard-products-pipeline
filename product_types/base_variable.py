from utilities.transformer import Transformer
from utilities import logger
import re

class BaseVariable:

    def __init__(self, parent_product):
        self.transformer = Transformer(None)
        self.parent_product = parent_product
        self.described_value_domain = None
        self.value_list = None
        self.links = {}
        self.name = None
    
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
            logger.debug(e)
            logger.error(f"No prior version found for variable: {self.to_string()}")
    
    def set_value_list(self, value_list_string):
        value_list = [code for code in re.split(r'[\n|;|,]', value_list_string)]
        value_list = [value.strip() for value in value_list if len(value) > 0]
        if value_list:
            self.value_list = value_list

    def set_described_value_domain(self, described_value_domain):
        self.described_value_domain = self.parent_product._get_described_value_domain(described_value_domain)

    def set_codelist_links(self, codelist):
        codelists = self.parent_product._get_codelist_links(codelist)
        if codelists:
            self.links["codelist"] = codelists
    
    def to_string(self):
        return self.name