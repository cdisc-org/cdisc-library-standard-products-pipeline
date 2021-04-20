import pytest
from product_types.data_analysis.variable import Variable
from product_types.data_analysis.adamig import ADAMIG
from utilities.config import Config
from unittest.mock import patch
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_adamig_summary

@pytest.fixture()
def mock_variable_data():
    return {
        "Variable Name": "cool_variable",
        "Variable Label": "cool_label",
        "Type": "number",
        "Seq. For Order": 1,
        "CDISC Notes": "This is the best variable",
        "Core": "Perm",
        "Class": "cool_class",
        "Variable Grouping": "best_varset"
    }

def test_variable_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_variable_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    variable = Variable(mock_variable_data, adamig)
    assert variable.name == mock_variable_data.get("Variable Name")
    assert variable.label == mock_variable_data.get("Variable Label")
    assert variable.data_type == mock_variable_data.get("Type")
    assert variable.core == mock_variable_data.get("Core")
    assert "self" in variable.links
    self_link = variable.links.get("self")
    assert self_link.get("title") == mock_variable_data.get("Variable Label")
    assert self_link.get("href") == f"/mdr/adam/adamig-5-0/datastructures/{mock_variable_data.get('Class')}/variables/{mock_variable_data.get('Variable Name')}"
    assert "parentProduct" in variable.links
    assert variable.links.get("parentProduct") == mock_adamig_summary["_links"]["self"]

def test_variable_creation_with_invalid_link_characters(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_variable_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    mock_variable_data["Variable Name"] = "cool variable"
    mock_variable_data["Class"] = "cool class"
    variable = Variable(mock_variable_data, adamig)
    assert variable.name == mock_variable_data.get("Variable Name")
    assert variable.label == mock_variable_data.get("Variable Label")
    assert variable.data_type == mock_variable_data.get("Type")
    assert variable.core == mock_variable_data.get("Core")
    assert "self" in variable.links
    self_link = variable.links.get("self")
    variable_link_name = variable.transformer.format_name_for_link(mock_variable_data.get('Variable Name'))
    class_name = variable.transformer.format_name_for_link(mock_variable_data.get("Class"))
    assert self_link.get("title") == mock_variable_data.get("Variable Label")
    assert self_link.get("href") == f"/mdr/adam/adamig-5-0/datastructures/{class_name}/variables/{variable_link_name}"
    assert "parentProduct" in variable.links
    assert variable.links.get("parentProduct") == mock_adamig_summary["_links"]["self"]

def test_to_json(mock_library_client, 
                            mock_wiki_client, 
                            mock_adamig_summary, 
                            mock_variable_data):
    config = Config({
        constants.DATASTRUCTURES: "12345"
    })
    version = "5-0"
    adamig= ADAMIG(mock_wiki_client, mock_library_client,mock_adamig_summary,"adamig",version, config)
    variable = Variable(mock_variable_data, adamig)
    json_data = variable.to_json()
    assert json_data.get("_links") == variable.links
    assert json_data.get("simpleDatatype") == variable.data_type
    assert json_data.get("core") == variable.core
    assert json_data.get("ordinal") == variable.ordinal
    assert json_data.get("description") == variable.description
