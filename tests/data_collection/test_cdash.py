import pytest
from product_types.data_collection.cdash import CDASH
from utilities.config import Config
from unittest.mock import patch
from tests.conftest import mock_library_client, mock_wiki_client, mock_products_payload, \
                                mock_classes_data
from utilities import constants

@pytest.fixture()
def mock_summary():
    return {
        "name": "Test CDASH",
        "parentModel": "2-1",
        "_links": {
            "self": {
                "href": "/mdr/cdash/5-0",
                "title": "Test CDASH link",
                "type": "Test Foundational Model"
            }
        }
    }

@pytest.fixture()
def mock_domain_data():
    return {
        "list": {
            "entry": [
                {
                    "fields": {
                        "name": "Domain 1",
                        "label": "First Domain",
                        "ordinal": "1"
                    }
                },
                {
                    "fields": {
                        "name": "Domain 2",
                        "label": "Second Domain",
                        "ordinal": "2"
                    }
                }
            ]
        }
    }

@pytest.mark.parametrize("product_type", [
    ("cdash"),
])
def test_get_classes(mock_wiki_client, mock_library_client, mock_summary, mock_classes_data, product_type):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_summary,product_type,version, config)
    mock_wiki_client.get_wiki_table.return_value = mock_classes_data
    classes = cdash.get_classes()
    class_names = [c["fields"]["name"] for c in mock_classes_data["list"]["entry"]]
    for c in classes:
        assert c.get("name") in class_names
        assert c["_links"]["self"]["href"] == f"/mdr/{product_type}/{version}/classes/{c.get('name').replace(' ', '')}"
        assert c["_links"].get("parentProduct") == mock_summary["_links"]["self"]

@pytest.mark.parametrize("product_type", [
    ("cdash"),
])
def test_get_domains(mock_wiki_client, mock_library_client, mock_summary, mock_domain_data, product_type):
    config = Config({
        constants.DOMAINS: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_summary,product_type,version, config)
    mock_wiki_client.get_wiki_table.return_value = mock_domain_data
    domains = cdash.get_domains()
    domain_names = [c["fields"]["name"] for c in mock_domain_data["list"]["entry"]]
    for domain in domains:
        assert domain.get("name") in domain_names
        assert domain["_links"]["self"]["href"] == f"/mdr/{product_type}/{version}/domains/{domain.get('name').replace(' ', '')}"
        assert domain["_links"].get("parentProduct") == mock_summary["_links"]["self"]

@pytest.mark.parametrize("product_type", [
    ("cdash"),
])
def test_get_all_prior_versions(mock_wiki_client, mock_library_client, mock_summary, mock_products_payload, product_type):
    config = Config({})
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_summary,product_type,version, config)
    mock_library_client.get_api_json.return_value = mock_products_payload
    prior_versions = cdash._get_all_prior_versions()
    for version in prior_versions:
        assert version["href"].startswith(f"/mdr/{product_type}")