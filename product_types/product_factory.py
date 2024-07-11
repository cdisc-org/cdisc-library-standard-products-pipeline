import json
import requests
from datetime import datetime
from utilities.wiki_client import WikiClient
from utilities.library_client import LibraryClient
from utilities.transformer import Transformer
from utilities import constants
from product_types.data_tabulation.sdtm import SDTM
from product_types.data_tabulation.sendig import SENDIG
from product_types.data_tabulation.sdtmig import SDTMIG
from product_types.data_collection.cdash import CDASH
from product_types.data_collection.cdashig import CDASHIG
from product_types.data_analysis.adamig import ADAMIG
from product_types.data_analysis.adam import ADAM
from product_types.integrated.integrated import Integrated

class ProductFactory:
    def __init__(self, username, password, api_key, **args):
        self.wiki_client = WikiClient(username, password, args.pop('spec_grabber_doc',''))
        self.api_key = api_key
        self.foundational_models = ["sdtm", "cdash", "adam"]
        self.transformer = Transformer()
    
    def get_summary(self, document_id):
        expected_fields = set(["name", "label", "effectiveDate", "registrationStatus", \
            "source", "version", "priorVersion", "description", "parentModel", "sdtmVersion", "sdtmigVersion"])
        summary = {
            "_links": {},
        }
        data = self.wiki_client.get_wiki_table(document_id, "Summary")
        if data:
            summary_data = data["list"]["entry"][0]
        else:
            return None

        registrationStatus = summary_data["fields"].get("registrationStatus")
        for key in summary_data["fields"]:
            if key in expected_fields:
                if key == "version":
                    summary[key] = str(summary_data["fields"][key])
                elif key == "effectiveDate":
                    if registrationStatus == "Final":
                        summary[key] = datetime.fromtimestamp(summary_data["fields"][key]/1000).strftime('%Y-%m-%d')
                    else:
                        summary[key] = datetime.now().strftime('%Y-%m-%d')
                else:
                    summary[key] = summary_data["fields"][key]

        product_type = summary_data["fields"]["productType"].lower()
        version = self.transformer.replace_str(str(summary["version"]), ".", "-")
        type_label = "Implementation Guide" if product_type not in self.foundational_models else "Foundational Model"
        prior_version_href = ""
        self_href = ""
        if (version.startswith("tig-") and product_type.endswith("ig")):
            product = version.split("-")[0]
            v = version.split("-", 1)[1]
            product_subtype = product_type[:-len("ig")]
            self_href = f"/mdr/integrated/{product}/{v}/{product_subtype}"
            if summary.get("priorVersion"):
                prior_version = self.transformer.replace_str(str(summary['priorVersion']),'.', '-')
                prior_version_href = f"/mdr/integrated/{product}/{prior_version}/{product_subtype}"
        elif (product_type.startswith("adam")):
            self_href = f"/mdr/adam/{product_type}-{version}"
            if summary.get("priorVersion"):
                prior_version = self.transformer.replace_str(str(summary['priorVersion']),'.', '-')
                prior_version_href = f"/mdr/adam/{summary_data['fields']['productType'].lower()}-{prior_version}"
        else:
            self_href = f"/mdr/{product_type}/{version}"
            if summary.get("priorVersion"):
                prior_version = self.transformer.replace_str(str(summary['priorVersion']),'.', '-')
                prior_version_href = f"/mdr/{summary_data['fields']['productType'].lower()}/{prior_version}"

        summary["_links"]["self"] = {
            "href": self_href,
            "title": summary["label"],
            "type": type_label
        }

        if summary.get("priorVersion"):
            summary["_links"]["priorVersion"] = {
                "href": prior_version_href,
                "title": summary["label"].replace(str(summary["version"]).replace("-", "."), str(summary["priorVersion"]).replace("-", ".")),
                "type": type_label
            }
            del summary["priorVersion"]
        return product_type, version, summary
    
    def build_product(self, config):
        document_id = config.get(constants.SUMMARY)
        product_type, version, summary = self.get_summary(document_id)
        product_subtype = None
        if version.startswith("tig-"):
            product_subtype = product_type[:-len("ig")] if product_type.endswith("ig") else product_type
            product_type = f"integrated/{version.split('-')[0]}"
            version = f"{version.split('-', 1)[1]}"
            summary["version"] = version
        if product_type == "sdtm":
            return SDTM(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type == "sendig" or product_subtype == "send":
            return SENDIG(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type == "sdtmig" or product_subtype == "sdtm":
            return SDTMIG(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type == "cdash":
            return CDASH(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type == "cdashig" or product_subtype == "cdash":
            return CDASHIG(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type == "adam":
            return ADAM(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type.startswith("adam") or product_subtype == "adam":
            return ADAMIG(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
        elif product_type == "integrated":
            return Integrated(self.wiki_client, LibraryClient(self.api_key), summary, product_type, version, product_subtype, config)
