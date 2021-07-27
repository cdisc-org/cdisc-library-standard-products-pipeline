import pytest
from product_types.data_collection.cdash import CDASH
from product_types.data_collection.variable import Variable
from utilities.config import Config
from unittest.mock import patch
from tests.conftest import mock_library_client, mock_wiki_client, \
                                mock_classes_data, mock_cdash_summary
from utilities import constants

@pytest.fixture()
def mock_variable_data():
    return {
        "CDASH Variable": "coolvariable",
        "CDASH Variable Label": "cool_label",
        "Data Type": "number",
        "Order Number": 1,
        "CDISC Notes": "This is the best variable",
        "CDASHIG Core": "Perm",
        "Prompt": "answer this question?",
        "Question Text": "?",
        "DRAFT CDASH Definition": "plz do not use this variable",
        "Implementation Notes": "do not implement",
        "Mapping Instructions": "maps to nothing",
        "Domain": "cool_domain",
        "Observation Class": "cool_class"
    }

def test_variable_creation_with_domain(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    variable = Variable(mock_variable_data, cdash)
    assert variable.name == mock_variable_data.get("CDASH Variable")
    assert variable.label == mock_variable_data.get("CDASH Variable Label")
    assert variable.data_type == mock_variable_data.get("Data Type")
    assert variable.core == mock_variable_data.get("CDASHIG Core")
    assert variable.prompt == mock_variable_data.get("Prompt")
    assert variable.question_text == mock_variable_data.get("Question Text")
    assert variable.ordinal == str(mock_variable_data.get("Order Number"))
    assert variable.parent_domain_name == mock_variable_data.get("Domain")
    assert variable.parent_class_name == mock_variable_data.get("Observation Class")
    assert variable.definition == mock_variable_data.get("DRAFT CDASH Definition")
    assert variable.implementation_notes == mock_variable_data.get("Implementation Notes")
    assert variable.mapping_instructions == mock_variable_data.get("Mapping Instructions")
    assert "self" in variable.links
    assert "parentProduct" in variable.links
    assert "rootItem" in variable.links
    self_link = variable.links.get("self")
    assert self_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/domains/{mock_variable_data.get('Domain')}/fields/{mock_variable_data.get('CDASH Variable')}"
    root_link = variable.links.get("rootItem")
    assert root_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert root_link.get("href") == f"/mdr/root/cdash/domains/{mock_variable_data.get('Domain')}/fields/{mock_variable_data.get('CDASH Variable')}"
    assert variable.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_variable_creation_with_class(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    mock_variable_data["Domain"] = None
    variable = Variable(mock_variable_data, cdash)
    assert variable.name == mock_variable_data.get("CDASH Variable")
    assert variable.label == mock_variable_data.get("CDASH Variable Label")
    assert variable.data_type == mock_variable_data.get("Data Type")
    assert variable.core == mock_variable_data.get("CDASHIG Core")
    assert variable.prompt == mock_variable_data.get("Prompt")
    assert variable.question_text == mock_variable_data.get("Question Text")
    assert variable.ordinal == str(mock_variable_data.get("Order Number"))
    assert variable.parent_domain_name == mock_variable_data.get("Domain")
    assert variable.parent_class_name == mock_variable_data.get("Observation Class")
    assert variable.definition == mock_variable_data.get("DRAFT CDASH Definition")
    assert variable.implementation_notes == mock_variable_data.get("Implementation Notes")
    assert variable.mapping_instructions == mock_variable_data.get("Mapping Instructions")
    assert "self" in variable.links
    assert "parentProduct" in variable.links
    assert "rootItem" in variable.links
    self_link = variable.links.get("self")
    assert self_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/classes/{mock_variable_data.get('Observation Class')}/fields/{mock_variable_data.get('CDASH Variable')}"
    root_link = variable.links.get("rootItem")
    assert root_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert root_link.get("href") == f"/mdr/root/cdash/classes/{mock_variable_data.get('Observation Class')}/fields/{mock_variable_data.get('CDASH Variable')}"
    assert variable.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]

def test_domain_variable_creation_with_invalid_link_characters(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    mock_variable_data["Domain"] = "cool domain"
    mock_variable_data["CDASH Variable"] = "cool variable"
    variable = Variable(mock_variable_data, cdash)
    self_link = variable.links.get("self")
    domain_name = variable.transformer.format_name_for_link(mock_variable_data.get("Domain"))
    variable_name = variable.transformer.format_name_for_link(mock_variable_data.get("CDASH Variable"))
    assert self_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/domains/{domain_name}/fields/{variable_name}"
    root_link = variable.links.get("rootItem")
    assert root_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert root_link.get("href") == f"/mdr/root/cdash/domains/{domain_name}/fields/{variable_name}"

def test_class_variable_creation_with_invalid_link_characters(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    mock_variable_data["Domain"] = None
    mock_variable_data["Observation Class"] = "class.name with invalid characters"
    mock_variable_data["CDASH Variable"] = "cool variable"
    variable = Variable(mock_variable_data, cdash)
    self_link = variable.links.get("self")
    class_name = variable.transformer.format_name_for_link(mock_variable_data.get("Observation Class"))
    variable_name = variable.transformer.format_name_for_link(mock_variable_data.get("CDASH Variable"))
    assert self_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert self_link.get("href") == f"/mdr/cdash/5-0/classes/{class_name}/fields/{variable_name}"
    root_link = variable.links.get("rootItem")
    assert root_link.get("title") == mock_variable_data.get("CDASH Variable Label")
    assert root_link.get("href") == f"/mdr/root/cdash/classes/{class_name}/fields/{variable_name}"

def test_to_json(mock_wiki_client, mock_library_client, mock_cdash_summary, mock_variable_data):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    variable = Variable(mock_variable_data, cdash)
    json_data = variable.to_json()
    assert json_data.get("_links") == variable.links
    assert json_data.get("label") == variable.label
    assert json_data.get("name") == variable.name
    assert json_data.get("ordinal") == variable.ordinal
    assert json_data.get("simpleDatatype") == variable.data_type
    assert json_data.get("prompt") == variable.prompt
    assert json_data.get("questionText") == variable.question_text
    assert json_data.get("mappingInstructions") == variable.mapping_instructions
    assert json_data.get("implementationNotes") == variable.implementation_notes

@pytest.mark.parametrize("parent_class_name, expected_mapping_type", [
    ("Domain Specific", "sdtmig"),
    ("Findings", "sdtm")
])
def test_get_variable_mapping_target_type(mock_wiki_client,
                                            mock_library_client,
                                            mock_cdash_summary,
                                            mock_variable_data,
                                            parent_class_name,
                                            expected_mapping_type):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    variable = Variable(mock_variable_data, cdash)
    variable.parent_class_name = parent_class_name
    mapping_target_type = variable._get_mapping_target_type()
    assert mapping_target_type == expected_mapping_type


@pytest.mark.parametrize("parent_class_name, parent_domain_name, target, expected_variable_type", [
    ("Domain Specific", "Test", "TEST", "Dataset"),
    ("Identifiers", None, "TSVAL", "Dataset"),
    ("Identifiers", None, "CO.COVAL", "Dataset"),
    ("Identifiers", None, "SUPP--.QVAL", "Dataset"),
    ("Identifiers", None, "SUPPDM.QVAL", "Dataset"),
    ("Identifiers", "DM", "CoolTarget", "Dataset"),
    ("Identifiers", None, "DM.CoolTarget", "Dataset"),
    ("Interventions", "LS", "CoolTarget", "Class"),
    ("Findings", "LS", "CoolTarget", "Class"),
    ("Events", "LS", "CoolTarget", "Class"),
    ("Findings About", "LS", "CoolTarget", "Class"),
])
def test_get_variable_mapping_target_variable_type(mock_wiki_client,
                                            mock_library_client,
                                            mock_cdash_summary,
                                            mock_variable_data,
                                            parent_class_name,
                                            parent_domain_name,
                                            target,
                                            expected_variable_type):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    variable = Variable(mock_variable_data, cdash)
    variable.parent_class_name = parent_class_name
    variable.parent_domain_name = parent_domain_name
    mapping_target_type = variable._get_mapping_target_variable_type(target)
    assert mapping_target_type == expected_variable_type

@pytest.mark.parametrize("parent_class_name, parent_domain_name, target, expected_parent", [
    ("Domain Specific", "QR", "TEST", "QR"),
    ("Identifiers", None, "TSVAL", "TS"),
    ("Identifiers", None, "CO.COVAL", "CO"),
    ("Identifiers", None, "SUPP--.QVAL", "SUPPQUAL"),
    ("Identifiers", None, "SUPPDM.QVAL", "SUPPQUAL"),
    ("Identifiers", "DM", "CoolTarget", "DM"),
    ("Identifiers", None, "DM.CoolTarget", "DM"),
    ("Interventions", "LS", "CoolTarget", "Interventions"),
    ("Findings", "LS", "CoolTarget", "Findings"),
    ("Events", "LS", "CoolTarget", "Events"),
    ("Findings About", "LS", "CoolTarget", "Findings About"),
])
def test_get_mapping_parent(mock_library_client,
                            mock_cdash_summary,
                            mock_variable_data,
                            parent_class_name,
                            parent_domain_name,
                            target,
                            expected_parent):
    config = Config({
        constants.CLASSES: "12345"
    })
    version = "5-0"
    cdash = CDASH(mock_wiki_client, mock_library_client,mock_cdash_summary,"cdash",version, config)
    variable = Variable(mock_variable_data, cdash)
    variable.parent_class_name = parent_class_name
    variable.parent_domain_name = parent_domain_name
    mapping_parent = variable._get_mapping_parent(target)
    assert mapping_parent == expected_parent
