import pytest
from product_types.data_analysis.datastructure import Datastructure
from product_types.data_analysis.adamig import ADAMIG
from utilities.config import Config
from unittest.mock import patch, Mock
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_adamig_summary

@pytest.fixture()
def mock_datastructure_data():
    return {
        "name": "cool_datastructure",
        "label": "cool_label",
        "description": "this is actually the best datastructure",
        "ordinal": 1
    }

def test_datastructure_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_datastructure_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    datastructure = Datastructure(mock_datastructure_data, adamig)
    assert datastructure.name == mock_datastructure_data.get("name")
    assert datastructure.label == mock_datastructure_data.get("label")
    assert datastructure.ordinal == str(mock_datastructure_data.get("ordinal"))
    assert datastructure.description == mock_datastructure_data.get("description")
    assert "self" in datastructure.links
    self_link = datastructure.links.get("self")
    assert self_link.get("title") == mock_datastructure_data.get("label")
    assert self_link.get("href") == f"/mdr/adam/adamig-5-0/datastructures/{mock_datastructure_data.get('name')}"
    assert "parentProduct" in datastructure.links
    assert datastructure.links.get("parentProduct") == mock_adamig_summary["_links"]["self"]

def test_datastructure_creation_with_invalid_link_characters(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_datastructure_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    mock_datastructure_data["name"] == "name with.invalid characters"
    datastructure = Datastructure(mock_datastructure_data, adamig)
    assert datastructure.name == mock_datastructure_data.get("name")
    assert datastructure.label == mock_datastructure_data.get("label")
    assert datastructure.ordinal == str(mock_datastructure_data.get("ordinal"))
    assert datastructure.description == mock_datastructure_data.get("description")
    assert "self" in datastructure.links
    self_link = datastructure.links.get("self")
    datastructure_name = datastructure.transformer.format_name_for_link(mock_datastructure_data.get("name"))
    assert self_link.get("title") == mock_datastructure_data.get("label")
    assert self_link.get("href") == f"/mdr/adam/adamig-5-0/datastructures/{datastructure_name}"
    assert "parentProduct" in datastructure.links
    assert datastructure.links.get("parentProduct") == mock_adamig_summary["_links"]["self"]

def test_to_json(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_datastructure_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    datastructure = Datastructure(mock_datastructure_data, adamig)
    json_data = datastructure.to_json()
    assert json_data.get("_links") == datastructure.links
    assert json_data.get("name") == datastructure.name
    assert json_data.get("ordinal") == datastructure.ordinal
    assert json_data.get("label") == datastructure.label


# From PBI 3003 conversion from single values to list values    
def test_codelist_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_adam_variable_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    mock = Mock(return_value=("latest","C66769"))
    adamig._get_concept_data = mock
    adam_variable = adamig._build_variable(mock_adam_variable_data)
    assert isinstance(adam_variable.links['codelist'],list)
    for codelist in adam_variable.links['codelist']:
        assert codelist['href'].endswith('C66769')