import requests
import json
from utilities import logger

class WikiClient:
    
    def __init__(self, username: str, password: str, spec_doc_id: str):
        self.username = username
        self.password = password
        self.spec_doc_id = spec_doc_id
        self.content_api_base_url = "https://wiki.cdisc.org/rest/api/content/"
        self.macros = {
            "summary": "35f2235a-e526-4b40-ad26-8161cd9defd7"
        }

    def get_wiki_json(self, document_id, doc_format = "view"):
        return self.get_json(self.content_api_base_url+f"{document_id}?expand=body.{doc_format}")
    
    def get_json(self, url):
        raw_data = requests.get(url, auth=(self.username, self.password))
        if raw_data.status_code == 200:
            if not raw_data.encoding:
                raw_data.encoding = 'UTF-8'
            return json.loads(raw_data.text)
        else:
            raise Exception(f"Get request to {url} returned unsuccessful response {raw_data.status_code}")
    
    def put_json(self, url, data):
        raw_data = requests.put(url, data, auth=(self.username, self.password), headers={"Content-Type": "application/json"})
        if raw_data.status_code != 200:
            raise Exception(f"Put request to {url} returned unsuccessful response {raw_data.status_code}")
        
    def get_wiki_table(self, document_id, table_name):
        base_url = f"https://wiki.cdisc.org/ajax/confiforms/rest/filter.action?pageId={document_id}&f={table_name}&q="
        response = requests.get(base_url, auth=(self.username, self.password))
        if response.status_code != 200:
            raise Exception(f"Invalid url for wiki document {document_id} and table {table_name}")
        return json.loads(response.text)
    
    def update_spec_grabber_content(self, product_type, version):
        document_url = self.content_api_base_url + self.spec_doc_id
        document_data = self.get_json(document_url)
        document_version = document_data["version"]["number"]
        with open("spec-grabber-template.json") as f:
            post_value = json.load(f)
        space_name, tables_name = self._get_spec_grabber_targets(product_type, version)
        post_value["value"] = post_value["value"].format(space_name, tables_name)
        document_data["version"]["number"] = document_data["version"]["number"] + 1
        post_data = {
            "version": document_data["version"],
            "title": document_data["title"],
            "type": document_data["type"],
            "space": document_data["space"],
            "body": {
                "storage": post_value
            }
        }
        self.put_json(document_url, json.dumps(post_data))
        return self.spec_doc_id
    
    def _get_spec_grabber_targets(self, product_type, version):
        version_number = self._get_version_number(version)
        target_mapping = {
            "sdtm": ("SDTM"+str(version).replace("-", "DOT").replace(".", "DOT"), "SDTM tables"),
            "sendig": ("SENDIG", "SENDIG domain tables"),
            "adamig": (product_type.upper() + str(version).replace("-", "DOT").replace(".", "DOT"), "ADaMIG tables"),
            "cdash": ("CMIG" + str(version_number+1).replace("-", "DOT").replace(".", "DOT"), "The CDASH Model"),
            "cdashig": ("CMIG" + str(version).replace("-", "DOT").replace(".", "DOT"), "CDASHIG Metadata Tables")
        }
        default_space_name = product_type.upper() + str(version).replace("-", "DOT").replace(".", "DOT")
        default_tables_name = product_type.upper() + " tables"
        return target_mapping.get(product_type, (default_space_name, default_tables_name))

    def _get_version_number(self, version):
        version = version.replace("-", ".")
        version_values = [int(x, 10) for x in version.split('.')]
        version_number = 0.0
        for i, value in enumerate(version_values):
            version_number = version_number + (value/(10.0**i))
        return version_number
