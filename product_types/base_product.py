import json
import codecs
import requests
import csv
import sys
import re
from bs4 import BeautifulSoup
from utilities.transformer import Transformer
from utilities import logger
import utilities.constants as constants

class BaseProduct:
    def __init__(self, wiki_client, library_client, summary, product_type, version, config = None):
        self.wiki_client = wiki_client
        self.config = config
        self.library_client = library_client
        self.transformer = Transformer(config)
        self.summary = summary
        self.product_type = product_type
        self.product_category = "base"
        self.codelist_types = []
        self.version = version
        self.version_number = self._get_version_number(version)
        self.version_prefix = self._get_version_prefix(version)
        self.has_parent_model = self.summary.get("parentModel")
        self.codelist_mapping = {}
        self.class_name_mappings = {
            'All Classes-General': "General Observations",
            "Interventions-General": "Interventions",
            "Events-General": "Events",
            "Findings-General": "Findings",
            "Findings About-Findings": "Findings About"
        }
        logger.info(f"Loading product of type: {product_type}")
        
    def _get_version_prefix(self, version: str) -> str:
        """
        Pulls the leading characters from version string.
        """
        prefix = ""
        for c in version:
            if c.isdigit():
                break
            else:
                prefix = prefix + c
        return prefix
    
    def _get_version_number(self, version: str) -> str:
        i = 0;
        for c in version:
            if c.isdigit():
                break
            else:
                i = i+1
        return version[i:]


    def generate_document(self, document_id: str) -> dict:
        raise NotImplementedError

    def _get_all_prior_versions(self) -> [dict]:
        """ returns all versions of a product returned by the /mdr/products CDISC library endpoint. """
        try:
            data = self.library_client.get_api_json("/mdr/products")
            if self.model_type == "adam":
                versions = data["_links"][self.product_category]["_links"].get("adam", [])
            else:
                versions = data["_links"][self.product_category]["_links"].get(self.product_type, [])
            return [version for version in versions if \
                        self._get_version_number(version["href"].split("/")[3]) < self.version_number and \
                            self._get_version_prefix(version["href"].split("/")[3]) == self.version_prefix ]
        except Exception as e:
            logger.error(e)
            return []
        return []


    def _get_prior_version(self, link: str) -> dict:
        prior_versions = self._get_all_prior_versions()
        data_link = '/'.join(link["href"].split('/')[4:])
        # Sort prior versions
        sorted_versions = sorted(prior_versions, key=lambda version: version["href"].split("/")[3])
        for version in reversed(sorted_versions):
            try:
                return self.library_client.get_api_json(version["href"] + "/" + data_link)["_links"]["self"]
            except:
                pass
        return None
    
    def write_document(self, document: dict, output_file: str = None):
        if not output_file:
            output_file = self.summary["name"].replace(" ", "") + ".json"
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=4, ensure_ascii=False)
    
    def _get_variable_prior_version(self, root_link: str) -> dict:
        try:
            root_data = self.library_client.get_api_json(root_link["href"])
            versions = root_data["_links"]["versions"]
            filtered_versions = [v for v in versions if self._get_version_prefix(v["href"].split("/")[3]) == self.version_prefix]
            if len(filtered_versions) >= 1:
                sorted_versions = sorted(filtered_versions, key=lambda version: version["href"].split("/")[3])
                for version in reversed(sorted_versions):
                    if self._get_version_number(version["href"].split("/")[3]) < self.version_number:
                        return version
        except Exception as e:
            logger.error(e)
            return None
        return None
        
    def validate_document(self, document: dict):
        pass

    def _parse_spec_grabber_output(self, output: str) -> csv.DictReader:
        parser = BeautifulSoup(output, 'html.parser')
        errors = self._parse_spec_grabber_errors(output)
        if errors:
            for error in errors:
                logger.error(f"Spec grabber scrape error found: {error}")
            if not self.config.get(constants.IGNORE_ERRORS):
                logger.error("Metadata pipeline unable to proceed due to spec grabber errors. Please fix them or use the -i (--ignore_errors) flag to ignore them.")
                sys.exit(1)
            else:
                logger.error("IGNORING SPEC GRABBER ERRORS")
        data_table = parser.find("pre")
        rows = data_table.string.splitlines()
        headers = [ x for x in list(csv.reader([rows[0]], delimiter=',', quotechar='"'))[0] ]
        return csv.DictReader(rows[1:], headers)
    
    def _parse_spec_grabber_errors(self, output):
        parser = BeautifulSoup(output, 'html.parser')
        info_table = parser.find("table", class_="confluenceTable")
        table = info_table.find("tbody")
        rows = table.find_all("tr")
        errors = []
        for row in rows:
            if "Scrape Errors" in row.text:     
                errors_list = row.find_all("li")
                for error in errors_list:        
                    errors.append(error.text)
        return errors

    def _validate_links(self, obj: dict):
        keys_to_validate = ["priorVersion", "model", "modelClassVariable", "codelist",  \
            "sdtmClassMappingTargets", "sdtmigDatasetMappingTargets"]
        if obj.get("_links"):
            for key, link in obj.get("_links").items():
                if key in keys_to_validate:
                    if isinstance(link, dict):
                        try:
                            self.library_client.get_api_json(link["href"])
                        except Exception as e:
                            logger.error(f"Get request failed for link: {link['href']}")
                    elif isinstance(link, list):
                        for l in link:
                            try:
                                self.library_client.get_api_json(l["href"])
                            except:
                                logger.error(f"Get request failed for link: {l['href']}")
                        
        else:
            logger.error(f"object with name {obj['name']} has no links")

    def _get_codelist_mapping(self) -> dict:
        codelist_json = self.library_client.get_api_json("/mdr/ct/packages")
        packages = codelist_json["_links"]["packages"]
        package_types = {
            "sendct": self._get_latest_codelist_with_type("send", packages),
            "sdtmct": self._get_latest_codelist_with_type("sdtm", packages),
            "adamct": self._get_latest_codelist_with_type("adam", packages)
        }
        codelist_mapping = {
            "sendct": {},
            "sdtmct": {},
            "adamct": {}
        }
        for package_type, latest_package in package_types.items():
            logger.debug(f"Building map of submissionValue -> concept id for {package_type} using latest package {latest_package}")
            try:
                codelist_spec = self.library_client.get_api_json(latest_package)
                for codelist in codelist_spec["codelists"]:
                    codelist_mapping[package_type][codelist["submissionValue"]] = codelist["conceptId"]
            except:
                logger.error(f"Unable to find latest codelist for package type {package_type} with link {latest_package}")
                continue
        return codelist_mapping
    
    def _get_codelist_links(self, codelist: str) -> [dict]:
        if not codelist or not codelist.startswith("("):
            return None
        codelist_array = [ct for ct in re.split(r'[\n|;|\\n]', codelist) if ct]
        codelists = []
        for ct in codelist_array:
            ct = ct.strip()
            # remove parenthesis
            ct = ct.replace("(", "").replace(")", "")
            codelist_type, concept_id = self._get_concept_data(ct)
            if concept_id:
                codelists.append(self._build_codelist_link(codelist_type, concept_id))
        return codelists
    
    def _get_described_value_domain(self, codelist: str) -> str:
        described_value_domain_mapping = {
            "nullflavor": "ISO 21090 NullFlavor enumeration",
        }
        return described_value_domain_mapping.get(codelist.lower(), codelist)
    
    def _get_concept_data(self, codelist_term: str) -> (str, str):
        for codelist_type in self.codelist_types:
            codelist_map = self.codelist_mapping.get(codelist_type)
            if codelist_map:
                concept_id = codelist_map.get(codelist_term)
                if concept_id:
                    logger.debug(f"Found a matching concept id for term {codelist_term}: {concept_id}")
                    return codelist_type, concept_id
        logger.error(f"Failed finding a matching concept id for codelist term {codelist_term}")
        return None, None

    def _get_latest_codelist_with_type(self, codelist_type: str, packages: [dict]) -> str:
        codelists = [package for package in packages if package["title"].lower().startswith(codelist_type)]
        if codelists:
            return codelists[-1]["href"]
        else:
            return None

        
    def _build_codelist_link(self, codelist_type: str, concept_id: str,) -> dict:
        return {
            "href": f"/mdr/root/ct/{codelist_type}/codelists/{concept_id}",
            "title": f"Version-agnostic anchor resource for codelist {concept_id}",
            "type": "Root Value Domain"
        }

    def _iscodelist(self, codelist: str) -> bool:
        return codelist.startswith("(")

    def _isdescribedvaluedomain(self, described_value_domain: str) -> bool:
        return described_value_domain.lower() in ["iso 8601", "nullflavor", "meddra", "number-number"]

    @staticmethod
    def _cleanup_json(json_data: dict, unwanted_keys: [str]):
        for key in unwanted_keys:
            if key in json_data:
                del json_data[key]

        invalid_keys = [k for k in json_data.keys() if json_data[k] in ["N/A", "", None]]
        for key in invalid_keys:
            del json_data[key]

    def _build_model_link(self) -> dict:
        model_title_map = {
            "cdash": "Clinical Data Acquisition Standards Harmonization Model Version {}",
            "sdtm": "Study Data Tabulation Model Version {}",
            "adam":"Analysis Data Model Version {}"
        }
        if self.model_type == "adam":
            version_string = self.model_type + "-" + self.transformer.replace_str(str(self.summary.get("parentModel")), ".", "-")
        else:
            version_string = self.transformer.replace_str(str(self.summary.get("parentModel")), ".", "-")
        href =f"/mdr/{self.model_type}/{version_string}"
        try:
            model_data = self.library_client.get_api_json(href)["_links"]["self"]
        except Exception as e:
            logger.error(f"{self.model_type.upper()} model version {version_string} does not exist in library. Building link manually")
            model_data = {
                "href": href,
                "title": model_title_map[self.model_type].format(self.summary.get("parentModel")),
                "type": "Foundational Model"             
            }
        self.parent_model = self.summary.get("parentModel")
        del self.summary["parentModel"]
        return model_data