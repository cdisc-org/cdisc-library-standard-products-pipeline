import pytest
from product_types.data_collection.cdash import CDASH
from product_types.data_collection.data_collection_class import DataCollectionClass
from utilities.config import Config
from unittest.mock import patch
from tests.conftest import mock_library_client, mock_wiki_client, \
                                mock_classes_data, mock_cdash_summary
from utilities import constants

@pytest.fixture()
def mock_class_data():
    return {
        "name": "coolclass",
        "label": "class label",
        "parentClass": "Findings",
        "ordinal": 1,
        "description": "this is the best class"
    }

def test_class_creation(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_class_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    class_obj = DataCollectionClass(mock_class_data, cdash)
    assert class_obj.name == mock_class_data.get("name")
    assert class_obj.label == mock_class_data.get("label")
    assert class_obj.ordinal == str(mock_class_data.get("ordinal"))
    assert class_obj.description == mock_class_data.get("description")
    assert "self" in class_obj.links
    assert "parentProduct" in class_obj.links
    self_link = class_obj.links.get("self")
    assert self_link.get("title") == mock_class_data.get("label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/classes/{mock_class_data.get('name')}"
    assert class_obj.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_class_creation_with_invalid_link_characters(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_class_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    mock_class_data["name"] = "invalid class.name /"
    class_obj = DataCollectionClass(mock_class_data, cdash)
    assert class_obj.name == mock_class_data.get("name")
    assert class_obj.label == mock_class_data.get("label")
    assert class_obj.ordinal == str(mock_class_data.get("ordinal"))
    assert class_obj.description == mock_class_data.get("description")
    assert "self" in class_obj.links
    assert "parentProduct" in class_obj.links
    self_link = class_obj.links.get("self")
    class_name = class_obj.transformer.format_name_for_link(mock_class_data.get("name"))
    assert self_link.get("title") == mock_class_data.get("label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/classes/{class_name}"
    assert class_obj.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_to_json(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_class_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    class_obj = DataCollectionClass(mock_class_data, cdash)
    json_data = class_obj.to_json()
    assert json_data.get("_links") == class_obj.links
    assert json_data.get("label") == class_obj.label
    assert json_data.get("name") == class_obj.name
    assert json_data.get("ordinal") == class_obj.ordinal
    assert json_data.get('description') == class_obj.description