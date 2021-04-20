import pytest
from product_types.data_collection.cdash import CDASH
from product_types.data_collection.scenario import Scenario
from utilities.config import Config
from unittest.mock import patch
from tests.conftest import mock_library_client, mock_wiki_client, \
                                mock_classes_data, mock_cdash_summary
from utilities import constants

@pytest.fixture()
def mock_scenario_data():
    return {
        "name": "coolscenario",
        "label": "scenario label",
        "implementationOption": False,
        "parentDomain": "DM",
        "parentClass": "Findings",
        "ordinal": 1
    }

def test_scenario_creation(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_scenario_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    scenario = Scenario(mock_scenario_data, cdash)
    assert scenario.name == mock_scenario_data.get("name")
    assert scenario.label == mock_scenario_data.get("label")
    assert scenario.parent_domain_name == mock_scenario_data.get("parentDomain")
    assert scenario.parent_class_name == mock_scenario_data.get("parentClass")
    assert "self" in scenario.links
    assert "parentProduct" in scenario.links
    self_link = scenario.links.get("self")
    assert self_link.get("title") == mock_scenario_data.get("label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/scenarios/{mock_scenario_data.get('parentDomain')}.{mock_scenario_data.get('name')}"
    assert scenario.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_scenario_creation_with_invalid_link_characters(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_scenario_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    mock_scenario_data["parentDomain"] = "D M"
    mock_scenario_data["name"] = "cool scenario"
    scenario = Scenario(mock_scenario_data, cdash)
    assert scenario.name == mock_scenario_data.get("name")
    assert scenario.label == mock_scenario_data.get("label")
    assert scenario.parent_domain_name == mock_scenario_data.get("parentDomain")
    assert scenario.parent_class_name == mock_scenario_data.get("parentClass")
    assert "self" in scenario.links
    assert "parentProduct" in scenario.links
    self_link = scenario.links.get("self")
    domain_name = scenario.transformer.format_name_for_link(mock_scenario_data.get('parentDomain'))
    scenario_name = scenario.transformer.format_name_for_link(mock_scenario_data.get('name'))
    assert self_link.get("title") == mock_scenario_data.get("label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/scenarios/{domain_name}.{scenario_name}"
    assert scenario.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_to_json(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_scenario_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    scenario = Scenario(mock_scenario_data, cdash)
    json_data = scenario.to_json()
    assert json_data.get("_links") == scenario.links
    assert json_data.get("label") == scenario.label
    assert json_data.get("name") == scenario.name
    assert json_data.get("ordinal") == scenario.ordinal
    assert json_data.get("scenario") == scenario.scenario