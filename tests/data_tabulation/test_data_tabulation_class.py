import pytest
from product_types.data_tabulation.data_tabulation_class import DataTabulationClass
from product_types.data_tabulation.sdtm import SDTM
from utilities.config import Config
from unittest.mock import patch
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_sdtm_summary

@pytest.fixture()
def mock_class_data():
    return {
        "name": "cool_class",
        "label": "cool_label",
        "description": "this is actually the best class",
        "ordinal": 1,
    }

def test_class_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_class_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    class_obj = DataTabulationClass(mock_class_data, "1", sdtm)
    assert class_obj.name == mock_class_data.get("name")
    assert class_obj.label == mock_class_data.get("label")
    assert class_obj.ordinal == str(mock_class_data.get("ordinal"))
    assert "self" in class_obj.links
    self_link = class_obj.links.get("self")
    assert self_link.get("title") == mock_class_data.get("label")
    assert self_link.get("href") == f"/mdr/sdtm/5-0/classes/{mock_class_data.get('name')}"
    assert "parentProduct" in class_obj.links
    assert class_obj.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]

def test_class_creation_with_invalid_link_characters(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_class_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    mock_class_data["name"] = "cool class"
    class_obj = DataTabulationClass(mock_class_data, "1", sdtm)
    assert class_obj.name == mock_class_data.get("name")
    assert class_obj.label == mock_class_data.get("label")
    assert class_obj.ordinal == str(mock_class_data.get("ordinal"))
    assert "self" in class_obj.links
    self_link = class_obj.links.get("self")
    assert self_link.get("title") == mock_class_data.get("label")
    class_name = class_obj.transformer.format_name_for_link(mock_class_data.get('name'))
    assert self_link.get("href") == f"/mdr/sdtm/5-0/classes/{class_name}"
    assert "parentProduct" in class_obj.links
    assert class_obj.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]

def test_to_json(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_class_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    class_obj = DataTabulationClass(mock_class_data, "1", sdtm)
    json_data = class_obj.to_json()
    assert "_links" in json_data
    assert json_data.get("name") == class_obj.name
    assert json_data.get("ordinal") == class_obj.ordinal
    assert json_data.get("label") == class_obj.label
    assert json_data.get("description") == class_obj.description 