import pytest
from product_types.data_analysis.adamig import ADAMIG
from utilities.config import Config
from unittest.mock import patch
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_products_payload

@pytest.fixture()
def mock_summary():
    return {
        "name": "Test ADAMIG",
        "parentModel": "2-1",
        "_links": {
            "self": {
                "href": "/mdr/adam/adamig-5-0",
                "title": "Test ADAMIG link",
                "type": "Test Implementation Guide"
            }
        }
    }

@pytest.fixture()
def mock_datastructure_data():
    return {
        "list": {
            "entry": [
                {
                    "fields": {
                        "name": "Datastructure 1",
                        "label": "First Datastructure",
                        "ordinal": "1",
                        "description": "Datastructure Description"
                    }
                },
                {
                    "fields": {
                        "name": "Datastructure 2",
                        "label": "Second Datastructure",
                        "ordinal": "2",
                        "description": "Datastructure Description"
                    }
                }
            ]
        }
    }

@pytest.fixture()
def mock_varset_data():
    return {
        "list": {
            "entry": [
                {
                    "fields": {
                        "name": "Varset 1",
                        "label": "First Varset",
                        "ordinal": "1",
                        "description": "Varset description",
                        "parentDatastructure": "Datastructure 1"
                    }
                },
                {
                    "fields": {
                        "name": "Varset 2",
                        "label": "Second Varset",
                        "ordinal": "2",
                        "description": "Varset description",
                        "parentDatastructure": "Datastructure 2"
                    }
                }
            ]
        }
    }

@pytest.mark.parametrize("product_type", [
    ("adamig"),
    ("adam-occds")
])
def test_get_datastructures(mock_wiki_client, mock_library_client, mock_summary, mock_datastructure_data, product_type):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_summary,product_type,version, config)
    mock_wiki_client.get_wiki_table.return_value = mock_datastructure_data
    datastructures = adamig.get_datastructures()
    datastructure_names = [c["fields"]["name"] for c in mock_datastructure_data["list"]["entry"]]
    version_string = product_type + "-" + version
    for datastructure in datastructures:
        assert datastructure.get("name") in datastructure_names
        assert datastructure["_links"]["self"]["href"] == f"/mdr/adam/{version_string}/datastructures/{datastructure.get('name').replace(' ', '')}"
        assert datastructure["_links"].get("parentProduct") == mock_summary["_links"]["self"]

@pytest.mark.parametrize("product_type", [
    ("adamig"),
    ("adam-occds")
])
def test_get_varsets(mock_wiki_client, mock_library_client, mock_summary, mock_varset_data, product_type):
    config = Config({
        constants.VARSETS: "12345"
    })
    version = "5-0"
    adamig = ADAMIG(mock_wiki_client, mock_library_client,mock_summary,product_type,version, config)
    mock_wiki_client.get_wiki_table.return_value = mock_varset_data
    varsets = adamig.get_varsets()
    varset_names = [c["fields"]["name"] for c in mock_varset_data["list"]["entry"]]
    version_string = product_type + "-" + version
    for varset in varsets:
        parent_datastructure = varset.get("parentDatastructure", "").replace(" ", "")
        assert varset.get("name") in varset_names
        assert varset["_links"]["self"]["href"] == f"/mdr/adam/{version_string}/datastructures/{parent_datastructure}/varsets/{varset.get('name').replace(' ', '')}"
        assert varset["_links"].get("parentProduct") == mock_summary["_links"]["self"]

@pytest.mark.parametrize("product_type", [
    ("adamig"),
    ("adam-occds")
])
def test_get_all_prior_versions(mock_wiki_client, mock_library_client, mock_summary, mock_products_payload, product_type):
    config = Config({})
    version = "5-0"
    adamig = ADAMIG(mock_wiki_client, mock_library_client,mock_summary,product_type,version, config)
    mock_library_client.get_api_json.return_value = mock_products_payload
    prior_versions = adamig._get_all_prior_versions()
    for version in prior_versions:
        assert version["href"].startswith(f"/mdr/adam/{product_type}")