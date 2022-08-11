from product_types.data_collection.variable import Variable
import pytest
from product_types.data_collection.cdash import CDASH
from utilities.config import Config
from tests.conftest import (
    mock_library_client,
    mock_wiki_client,
    mock_products_payload,
    mock_classes_data,
    mock_cdash_summary,
)
from utilities import constants


@pytest.fixture()
def mock_domain_data():
    return {
        "list": {
            "entry": [
                {
                    "fields": {
                        "name": "Domain 1",
                        "label": "First Domain",
                        "ordinal": "1",
                    }
                },
                {
                    "fields": {
                        "name": "Domain 2",
                        "label": "Second Domain",
                        "ordinal": "2",
                    }
                },
            ]
        }
    }


@pytest.fixture()
def mock_variable_data():
    return {
        "body": {
            "view": {
                "value": '<table class="confluenceTable"><tbody></tbody></table><pre>'
                + "Seq. for Order,Case Report Form Completion Instructions,SDTMIG Target,Question Text,Controlled Terminology Codelist Name,Implementation Options,Implementation Notes,CDASHIG Variable Label,CDASHIG Variable,Data Type,CDASHIG Core,DRAFT CDASHIG Definition,Observation Class,Prompt,Subset Controlled Terminology/CDASH Codelist Name,Domain,Data Collection Scenario,Mapping Instructions,Order Number"
                + "\n20,&quot;CRF Instr for CMDOSFRQ.&quot;,CMDOSFRQ,What was the CMDOSFRQ?,(FREQ),N/A,&quot;Impl Notes for CMDOSFRQ&quot;,CM Dosing Frequency per Interval,CMDOSFRQ,Char,O,Defininion for CMDOSFRQ.,Interventions,Frequency,(CMDOSFRQ),CM,N/A,Mapping Instr.,20"
                + "\n7,&quot;CRF Instr for DSDECOD.&quot;,DSDECOD,[Sponsor-defined],(PROTMLST);(OTHEVENT),N/A,&quot;Details for DSDECOD&quot;,Standardized Disposition Term,DSDECOD,Char,R/C,Definition of DSDECOD,Events,[Sponsor-defined],N/A,DS,PROTOCOL MILESTONE/OTHER EVENT,Mapping Instr for DSDECOD.,7"
                + "\n12,&quot;CRF Instr for IEORRES.&quot;,IEORRES,What is the result?,N/A,N/A,&quot;Impl Notes for IEORRES&quot;,I/E Criterion Original Result,IEORRES,Char,HR,IEORRES Description.,Findings,(Result),(NY),IE,N/A,Mapping Instr.,12"
                + "\n39,&quot;CRF instr for VSPOS.&quot;,VSPOS,Q for VSPOS?,(POSITION),N/A,&quot;VSPOS Impl notes.&quot;,Vital Signs Position of Subject,VSPOS,Char,R/C,Description for VSPOS.,Findings,Position,(VSPOS),VS,N/A,Mapping Instr.,20"
                + "</pre>"
            }
        }
    }


@pytest.mark.parametrize(
    "product_type",
    [
        ("cdash"),
    ],
)
def test_get_classes(
    mock_wiki_client,
    mock_library_client,
    mock_cdash_summary,
    mock_classes_data,
    product_type,
):
    config = Config({constants.CLASSES: "12345"})
    version = "5-0"
    cdash = CDASH(
        mock_wiki_client,
        mock_library_client,
        mock_cdash_summary,
        product_type,
        version,
        config,
    )
    mock_wiki_client.get_wiki_table.return_value = mock_classes_data
    classes = cdash.get_classes()
    class_names = [c["fields"]["name"] for c in mock_classes_data["list"]["entry"]]
    expected_output_keys = ["_links", "name", "ordinal", "label"]
    for c in classes:
        assert c.name in class_names
        assert (
            c.links["self"]["href"]
            == f"/mdr/{product_type}/{version}/classes/{c.name.replace(' ', '')}"
        )
        assert c.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]
        for key in expected_output_keys:
            assert key in c.to_json()


@pytest.mark.parametrize(
    "product_type",
    [
        ("cdash"),
    ],
)
def test_get_domains(
    mock_wiki_client,
    mock_library_client,
    mock_cdash_summary,
    mock_domain_data,
    product_type,
):
    config = Config({constants.DOMAINS: "12345"})
    version = "5-0"
    cdash = CDASH(
        mock_wiki_client,
        mock_library_client,
        mock_cdash_summary,
        product_type,
        version,
        config,
    )
    mock_wiki_client.get_wiki_table.return_value = mock_domain_data
    domains = cdash.get_domains()
    domain_names = [c["fields"]["name"] for c in mock_domain_data["list"]["entry"]]
    expected_output_keys = ["_links", "name", "ordinal", "label"]
    for domain in domains:
        assert domain.name in domain_names
        assert (
            domain.links["self"]["href"]
            == f"/mdr/{product_type}/{version}/domains/{domain.name.replace(' ', '')}"
        )
        assert domain.links.get("parentProduct") == mock_cdash_summary["_links"]["self"]
        for key in expected_output_keys:
            assert key in domain.to_json()


@pytest.mark.parametrize(
    "product_type",
    [
        ("cdash"),
    ],
)
def test_get_variable_codelists(
    mock_wiki_client,
    mock_library_client,
    mock_cdash_summary,
    mock_variable_data,
    product_type,
):
    config = Config({constants.VARIABLES: "12345"})
    version = "5-0"
    cdash = CDASH(
        mock_wiki_client,
        mock_library_client,
        mock_cdash_summary,
        product_type,
        version,
        config,
    )
    mock_wiki_client.get_wiki_json.return_value = mock_variable_data
    mock_library_client.get_api_json.side_effect = mock_products_payload
    cdash.codelist_mapping = cdash._get_codelist_mapping()
    variables = cdash.get_variables()
    assert len(variables) == 4
    # CMDOSFRQ - 1 sdtm codelist & 1 cdash subset
    assert len(variables[0].links["codelist"]) == 2
    # CMDOSFRQ - Codelist - FREQ
    assert (
        variables[0].links["codelist"][0]["href"]
        == "/mdr/root/ct/sdtmct/codelists/C71113"
    )
    # CMDOSFRQ - Subset Codelist - CMDOSFRQ
    assert (
        variables[0].links["codelist"][1]["href"]
        == "/mdr/root/ct/cdashct/codelists/C78419"
    )
    assert(variables[0].codelist_submission_values == ["FREQ", "CMDOSFRQ"])
    # DSDECOD - 2 sdtm codelists
    assert len(variables[1].links["codelist"]) == 2
    # DSDECOD - Codelist - PROTMLST
    assert (
        variables[1].links["codelist"][0]["href"]
        == "/mdr/root/ct/sdtmct/codelists/C114118"
    )
    # DSDECOD - Codelist - OTHEVENT
    assert (
        variables[1].links["codelist"][1]["href"]
        == "/mdr/root/ct/sdtmct/codelists/C150811"
    )
    assert(variables[1].codelist_submission_values == ["PROTMLST", "OTHEVENT"])
    # IEORRES - 1 sdtm subset
    assert len(variables[2].links["codelist"]) == 1
    # IEORRES - Codelist - NY
    assert (
        variables[2].links["codelist"][0]["href"]
        == "/mdr/root/ct/sdtmct/codelists/C66742"
    )
    assert(variables[2].codelist_submission_values == ["NY"])
    # VPOS - 1 sdtm codelist & 1 cdash subset
    assert len(variables[3].links["codelist"]) == 2
    # VPOS - Codelist - POSITION
    assert (
        variables[3].links["codelist"][0]["href"]
        == "/mdr/root/ct/sdtmct/codelists/C71148"
    )
    # VPOS - Subset Codelist - VSPOS
    assert (
        variables[3].links["codelist"][1]["href"]
        == "/mdr/root/ct/cdashct/codelists/C78431"
    )
    assert(variables[3].codelist_submission_values == ["POSITION", "VSPOS"])


@pytest.mark.parametrize(
    "product_type",
    [
        ("cdash"),
    ],
)
def test_get_all_prior_versions(
    mock_wiki_client, mock_library_client, mock_cdash_summary, product_type
):
    config = Config({})
    version = "5-0"
    cdash = CDASH(
        mock_wiki_client,
        mock_library_client,
        mock_cdash_summary,
        product_type,
        version,
        config,
    )
    mock_library_client.get_api_json.side_effect = mock_products_payload
    prior_versions = cdash._get_all_prior_versions()
    for version in prior_versions:
        assert version["href"].startswith(f"/mdr/{product_type}")
