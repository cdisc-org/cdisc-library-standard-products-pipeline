import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from functools import cache

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 502, 503, 504, 408],
    method_whitelist=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

class LibraryClient:

    def __init__(self, api_key):
        self.base_api_url = "https://dev.cdisclibrary.org/api"
        self.api_key = api_key

    @cache
    def get_api_json(self, href):
        headers = {
            'Accept': 'application/json',
            'api-key': self.api_key,
            "User-Agent": "cdisc-standard-product-pipeline"
        }
        raw_data = http.get(self.base_api_url+href, headers=headers)
        if raw_data.status_code == 200:
            return json.loads(raw_data.text)
        else:
            raise Exception(f"Request to {self.base_api_url+href} returned unsuccessful {raw_data.status_code} response")
    
    @cache
    def get_raw_response(self, href):
        headers = {
            'Accept': 'application/json',
            'api-key': self.api_key,
            "User-Agent": "pipeline"
        }
        return http.get(self.base_api_url+href, headers=headers)
    
    @cache
    def _create_lookup(self, href, query):
        json_data = self.get_api_json(href)
        keyed = query(json_data)
        return keyed

    @cache
    def query_api_json(self, href, query, key):
        lookup = self._create_lookup(href, query)
        match = lookup.get(key)
        return match
