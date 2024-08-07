from product_types.base_product import BaseProduct
from product_types.data_analysis.adamig import ADAMIG
from product_types.data_collection.cdashig import CDASHIG
from product_types.data_tabulation.sdtmig import SDTMIG
from product_types.data_tabulation.sendig import SENDIG

class Integrated(BaseProduct):
    def __init__(self, wiki_client, library_client, summary, product_type, version, product_subtype, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, product_subtype, config)
        self.product_category = "integrated"
        self.name = self.summary["name"].split(" ")[0]
        self.label = self.summary["label"]
        self.summary["_links"]["self"] = self.build_self_link()
        self.summary["_links"]["standards"] = {}
        self.models_links = set()
        self.summary["_links"]["models"] = []

    def build_self_link(self) -> dict:
        name = self.transformer.format_name_for_link(self.name)
        self_link = {
            "href": f"/mdr/integrated/{name.lower()}/{self.version}",
            "title": self.label, 
            "type": "Integrated Standard"
        }
        return self_link

    def _get_product_type(self, product: BaseProduct) -> str:
        if isinstance(product, ADAMIG):
            return "adam"
        elif isinstance(product, CDASHIG):
            return "cdash"
        elif isinstance(product, SDTMIG):
            return "sdtm"
        elif isinstance(product, SENDIG):
            return "send"
        else:
            return "unknown"

    def add_standard(self, product: BaseProduct):
        product_type = self._get_product_type(product)   
        self.summary["_links"]["standards"][product_type] = product.summary["_links"]["self"]
        if product.summary["_links"]["model"]["href"] not in self.models_links:
            self.summary["_links"]["models"].append(product.summary["_links"]["model"])
            self.models_links.add(product.summary["_links"]["model"]["href"])

    def _get_directory(self, document_id: str):
        return self.wiki_client.get_wiki_table(document_id, "Directory")

    def generate_config(self, entry: dict) -> dict:
        fields = entry["fields"]
        standard = fields["productType"]
        doc_id = self.wiki_client.get_page_id(fields['link'])
        standard_to_config_mapping = {
                "cdashig": self._generate_cdash_config,
                "sendig": self._generate_sdtm_config,
                "sdtmig": self._generate_sdtm_config,
                "adamig": self._generate_adam_config
        }
        return standard_to_config_mapping.get(standard)(doc_id)

    def _generate_adam_config(self, document_id: str) -> dict:
        return {
            "summary": document_id,
            "datastructures": document_id,
            "variableSets": document_id,
            "variables": document_id,
        }

    def _generate_sdtm_config(self, document_id: str) -> dict:
        return {
            "summary": document_id,
            "variables": document_id,
            "classMetadata": document_id,
            "datasetMetadata": document_id
        }
    
    def _generate_cdash_config(self, document_id: str) -> dict:
        return {
            "summary": document_id,
            "variables": document_id,
            "classMetadata": document_id,
            "domainsMetadata": document_id,
            "scenarioMetadata": document_id
        }

    def generate_document(self) -> dict:
        return self.summary
