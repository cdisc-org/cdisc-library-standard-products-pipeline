import pytest
from product_types.data_tabulation.dataset import Dataset
from product_types.data_tabulation.sdtm import SDTM
from utilities.config import Config
from unittest.mock import patch
from utilities import constants
from tests.conftest import mock_library_client, mock_wiki_client, mock_sdtm_summary

@pytest.fixture()
def mock_dataset_data():
    return {
        "name": "cool_dataset",
        "label": "cool_label",
        "description": "this is actually the best dataset",
        "ordinal": 1,
        "datasetStructure": "square"
    }

def test_dataset_creation(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_dataset_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    dataset = Dataset(mock_dataset_data, "1", sdtm)
    assert dataset.name == mock_dataset_data.get("name")
    assert dataset.label == mock_dataset_data.get("label")
    assert dataset.ordinal == str(mock_dataset_data.get("ordinal"))
    assert dataset.structure == mock_dataset_data.get("datasetStructure")
    assert "self" in dataset.links
    self_link = dataset.links.get("self")
    assert self_link.get("title") == mock_dataset_data.get("label")
    assert self_link.get("href") == f"/mdr/sdtm/5-0/datasets/{mock_dataset_data.get('name')}"
    assert "parentProduct" in dataset.links
    assert dataset.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]

def test_dataset_creation_with_invalid_link_characters(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_dataset_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    mock_dataset_data["name"] = "cool class"
    dataset = Dataset(mock_dataset_data, "1", sdtm)
    assert dataset.name == mock_dataset_data.get("name")
    assert dataset.label == mock_dataset_data.get("label")
    assert dataset.ordinal == str(mock_dataset_data.get("ordinal"))
    assert dataset.structure == mock_dataset_data.get("datasetStructure")
    assert "self" in dataset.links
    self_link = dataset.links.get("self")
    assert self_link.get("title") == mock_dataset_data.get("label")
    dataset_name = dataset.transformer.format_name_for_link(mock_dataset_data.get('name'))
    assert self_link.get("href") == f"/mdr/sdtm/5-0/datasets/{dataset_name}"
    assert "parentProduct" in dataset.links
    assert dataset.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]

def test_to_json(mock_library_client, 
                            mock_wiki_client, 
                            mock_sdtm_summary, 
                            mock_dataset_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(mock_wiki_client, mock_library_client,mock_sdtm_summary,product_type,version, config)
    dataset = Dataset(mock_dataset_data, "1", sdtm)
    json_data = dataset.to_json()
    assert "_links" in json_data
    assert json_data.get("name") == dataset.name
    assert json_data.get("datasetStructure") == dataset.structure
    assert json_data.get("ordinal") == dataset.ordinal
    assert json_data.get("label") == dataset.label
    assert json_data.get("description") == dataset.description 
