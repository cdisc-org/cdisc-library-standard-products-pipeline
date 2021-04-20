import pytest
from product_types.data_collection.cdash import CDASH
from product_types.data_collection.domain import Domain
from utilities.config import Config
from unittest.mock import patch
from tests.conftest import mock_library_client, mock_wiki_client, \
                                mock_classes_data, mock_cdash_summary
from utilities import constants

@pytest.fixture()
def mock_domain_data():
    return {
        "name": "cooldomain",
        "label": "domain label",
        "parentClass": "Findings",
        "ordinal": 1,
        "description": "this is the best domain"
    }

def test_domain_creation(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_domain_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    domain = Domain(mock_domain_data, cdash)
    assert domain.name == mock_domain_data.get("name")
    assert domain.label == mock_domain_data.get("label")
    assert domain.parent_class_name == mock_domain_data.get("parentClass")
    assert domain.ordinal == str(mock_domain_data.get("ordinal"))
    assert domain.description == mock_domain_data.get("description")
    assert "self" in domain.links
    assert "parentProduct" in domain.links
    self_link = domain.links.get("self")
    assert self_link.get("title") == mock_domain_data.get("label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/domains/{mock_domain_data.get('name')}"
    assert domain.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_domain_creation_with_invalid_link_characters(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_domain_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    mock_domain_data["name"] = "cool domain"
    domain = Domain(mock_domain_data, cdash)
    assert domain.name == mock_domain_data.get("name")
    assert domain.label == mock_domain_data.get("label")
    assert domain.parent_class_name == mock_domain_data.get("parentClass")
    assert domain.ordinal == str(mock_domain_data.get("ordinal"))
    assert domain.description == mock_domain_data.get("description")
    assert "self" in domain.links
    assert "parentProduct" in domain.links
    self_link = domain.links.get("self")
    domain_name = domain.transformer.format_name_for_link(mock_domain_data.get('name'))
    assert self_link.get("title") == mock_domain_data.get("label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/domains/{domain_name}"
    assert domain.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_to_json(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_domain_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    domain = Domain(mock_domain_data, cdash)
    json_data = domain.to_json()
    assert json_data.get("_links") == domain.links
    assert json_data.get("label") == domain.label
    assert json_data.get("name") == domain.name
    assert json_data.get("ordinal") == domain.ordinal
    assert json_data.get('description') == domain.description