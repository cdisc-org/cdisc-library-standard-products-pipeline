import pytest
from product_types.data_tabulation.variable import Variable
from product_types.data_tabulation.sdtm import SDTM
from utilities.config import Config
from unittest.mock import patch
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_sdtm_summary

@pytest.fixture()
def mock_variable_data():
    return {
        "Variable Name": "cool_variable",
        "Variable Label": "cool_label",
        "Type": "number",
        "Seq. For Order": 1,
        "CDISC Notes": "This is the best variable",
        "Core": "Perm",
        "Observation Class": "cool_class",
        "Format": "wingdings",
        "Usage Restrictions": "plz do not use this variable",
        "Definition": "the coolest variable",
        "Examples": ":)",
        "Notes": "See cdisc notes",
    }

def test_class_variable_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    variable = Variable(mock_variable_data, sdtm)
    assert variable.name == mock_variable_data.get("Variable Name")
    assert variable.examples == mock_variable_data.get("Examples")
    assert variable.label == mock_variable_data.get("Variable Label")
    assert variable.core == mock_variable_data.get("Core")
    assert variable.usage_restrictions == mock_variable_data.get("Usage Restrictions")
    assert variable.examples == mock_variable_data.get("Examples")
    assert variable.described_value_domain == mock_variable_data.get("Format")
    assert "self" in variable.links
    assert "rootItem" in variable.links
    self_link = variable.links.get("self")
    assert self_link.get("title") == mock_variable_data.get("Variable Label")
    assert self_link.get("href") == f"/mdr/sdtm/5-0/classes/{mock_variable_data.get('Observation Class')}/variables/{mock_variable_data.get('Variable Name')}"
    assert "parentProduct" in variable.links
    assert variable.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]
    root_link = variable.links.get("rootItem")
    assert root_link.get("title") == f"Version-agnostic anchor resource for SDTM variable {mock_variable_data.get('Observation Class')}.{mock_variable_data.get('Variable Name')}"
    assert root_link.get("href") == f"/mdr/root/sdtm/classes/{mock_variable_data.get('Observation Class')}/variables/{mock_variable_data.get('Variable Name')}"

def test_dataset_variable_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    mock_variable_data["Dataset Name"] = "DM"
    variable = Variable(mock_variable_data, sdtm)
    assert variable.name == mock_variable_data.get("Variable Name")
    assert variable.examples == mock_variable_data.get("Examples")
    assert variable.label == mock_variable_data.get("Variable Label")
    assert variable.core == mock_variable_data.get("Core")
    assert variable.usage_restrictions == mock_variable_data.get("Usage Restrictions")
    assert variable.examples == mock_variable_data.get("Examples")
    assert variable.described_value_domain == mock_variable_data.get("Format")
    assert "self" in variable.links
    assert "rootItem" in variable.links
    self_link = variable.links.get("self")
    assert self_link.get("title") == mock_variable_data.get("Variable Label")
    assert self_link.get("href") == f"/mdr/sdtm/5-0/datasets/{mock_variable_data.get('Dataset Name')}/variables/{mock_variable_data.get('Variable Name')}"
    assert "parentProduct" in variable.links
    assert variable.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]
    root_link = variable.links.get("rootItem")
    assert root_link.get("title") == f"Version-agnostic anchor resource for SDTM variable {mock_variable_data.get('Dataset Name')}.{mock_variable_data.get('Variable Name')}"
    assert root_link.get("href") == f"/mdr/root/sdtm/datasets/{mock_variable_data.get('Dataset Name')}/variables/{mock_variable_data.get('Variable Name')}"

def test_variable_creation_invalid_link_characters(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    mock_variable_data["Variable Name"] = "cool variable"
    mock_variable_data["Observation Class"] = "cool class"
    variable = Variable(mock_variable_data, sdtm)
    assert variable.name == mock_variable_data.get("Variable Name")
    assert variable.examples == mock_variable_data.get("Examples")
    assert variable.label == mock_variable_data.get("Variable Label")
    assert variable.core == mock_variable_data.get("Core")
    assert variable.usage_restrictions == mock_variable_data.get("Usage Restrictions")
    assert variable.examples == mock_variable_data.get("Examples")
    assert variable.described_value_domain == mock_variable_data.get("Format")
    assert "self" in variable.links
    assert "rootItem" in variable.links
    self_link = variable.links.get("self")
    assert self_link.get("title") == mock_variable_data.get("Variable Label")
    variable_link_name = variable.transformer.format_name_for_link(mock_variable_data.get('Variable Name'))
    class_name = variable.transformer.format_name_for_link(mock_variable_data.get("Observation Class"))
    assert self_link.get("href") == f"/mdr/sdtm/5-0/classes/{class_name}/variables/{variable_link_name}"
    assert "parentProduct" in variable.links
    assert variable.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]

def test_to_json(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    variable = Variable(mock_variable_data, sdtm)
    json_data = variable.to_json()
    assert "_links" in json_data
    assert json_data.get("name") == variable.name
    assert json_data.get("ordinal") == variable.ordinal
    assert json_data.get("label") == variable.label
    assert json_data.get("description") == variable.description 
    assert json_data.get("notes") == variable.notes
    assert json_data.get("core") == variable.core
    assert json_data.get("definition") == variable.definition
    assert json_data.get("describedValueDomain") == variable.described_value_domain
    assert json_data.get("usageRestrictions") == variable.usage_restrictions
