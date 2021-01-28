from product_types.base_product import BaseProduct
import csv
import sys
from copy import deepcopy

class ADAM(BaseProduct):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.product_category = "data-analysis"
        self.codelist_type = "sdtm"
        self.tabulation_mapping = "sdtm"
        self.model_type = "adam"
    
    def generate_document(self) -> dict:
        return self.summary