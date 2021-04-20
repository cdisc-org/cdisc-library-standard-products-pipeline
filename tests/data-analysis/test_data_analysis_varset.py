import pytest
from product_types.data_analysis.varset import Varset
from product_types.data_analysis.adamig import ADAMIG
from utilities.config import Config
from unittest.mock import patch
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_adamig_summary

@pytest.fixture()
def mock_varset_data():
    return {
        "name": "cool_varset",
        "label": "cool_label",
        "parentDatastructure": "cool_datastructure",
        "description": "this is actually the best varset",
        "ordinal": 1
    }

def test_varset_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_varset_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    varset = Varset(mock_varset_data, adamig)
    assert varset.name == mock_varset_data.get("name")
    assert varset.label == f'{mock_varset_data.get("parentDatastructure")} {mock_varset_data.get("label")}'
    assert varset.ordinal == str(mock_varset_data.get("ordinal"))
    assert varset.description == mock_varset_data.get("description")
    assert "self" in varset.links
    self_link = varset.links.get("self")
    assert self_link.get("title") == f'{mock_varset_data.get("parentDatastructure")} {mock_varset_data.get("label")}'
    assert self_link.get("href") == f"/mdr/adam/adamig-5-0/datastructures/{mock_varset_data.get('parentDatastructure')}/varsets/{mock_varset_data.get('name')}"
    assert "parentProduct" in varset.links
    assert varset.links.get("parentProduct") == mock_adamig_summary["_links"]["self"]

def test_varset_creation_with_invalid_link_characters(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_varset_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    mock_varset_data["name"] == "name with.invalid characters"
    mock_varset_data["parentDatastructure"] == "cool datastructure"
    varset = Varset(mock_varset_data, adamig)
    assert varset.name == mock_varset_data.get("name")
    assert varset.label == f'{mock_varset_data.get("parentDatastructure")} {mock_varset_data.get("label")}'
    assert varset.ordinal == str(mock_varset_data.get("ordinal"))
    assert varset.description == mock_varset_data.get("description")
    assert "self" in varset.links
    self_link = varset.links.get("self")
    varset_name = varset.transformer.format_name_for_link(mock_varset_data.get("name"))
    datastructure_name = varset.transformer.format_name_for_link(mock_varset_data.get("parentDatastructure"))
    assert self_link.get("title") == f'{mock_varset_data.get("parentDatastructure")} {mock_varset_data.get("label")}'
    assert self_link.get("href") == f"/mdr/adam/adamig-5-0/datastructures/{datastructure_name}/varsets/{varset_name}"
    assert "parentProduct" in varset.links
    assert varset.links.get("parentProduct") == mock_adamig_summary["_links"]["self"]

def test_to_json(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_varset_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    varset = Varset(mock_varset_data, adamig)
    json_data = varset.to_json()
    assert json_data.get("_links") == varset.links
    assert json_data.get("name") == varset.name
    assert json_data.get("ordinal") == varset.ordinal
    assert json_data.get("label") == varset.label