import pytest
from product_types.data_tabulation.sdtm import SDTM
from product_types.data_tabulation.variable import Variable
from utilities.config import Config
from utilities import constants
from unittest.mock import patch
from tests.conftest import (
    mock_library_client,
    mock_wiki_client,
    mock_classes_data,
    mock_products_payload,
    mock_sdtm_summary,
    mock_sdtm_variable_data,
)


@pytest.fixture()
def mock_dataset_data():
    return {
        "list": {
            "entry": [
                {
                    "fields": {
                        "name": "Dataset 1",
                        "label": "First Dataset",
                        "ordinal": "1",
                        "datsetStructure": "One record per subject",
                    }
                },
                {
                    "fields": {
                        "name": "Dataset 2",
                        "label": "Second Dataset",
                        "ordinal": "2",
                        "datsetStructure": "One record per subject",
                    }
                },
            ]
        }
    }


def test_get_classes(
    mock_wiki_client, mock_library_client, mock_sdtm_summary, mock_classes_data
):
    config = Config({constants.CLASSES: "12345"})
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(
        mock_wiki_client,
        mock_library_client,
        mock_sdtm_summary,
        product_type,
        version,
        config,
    )
    mock_wiki_client.get_wiki_table.return_value = mock_classes_data
    classes = sdtm.get_classes()
    class_names = [c["fields"]["name"] for c in mock_classes_data["list"]["entry"]]
    expected_output_keys = ["_links", "name", "ordinal", "label"]
    for c in classes:
        assert c.name in class_names
        assert (
            c.links["self"]["href"]
            == f"/mdr/{product_type}/{version}/classes/{c.name.replace(' ', '')}"
        )
        assert c.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]
        for key in expected_output_keys:
            assert key in c.to_json()


def test_get_datasets(
    mock_wiki_client, mock_library_client, mock_sdtm_summary, mock_dataset_data
):
    config = Config({constants.DATASETS: "12345"})
    version = "5-0"
    product_type = "sdtm"
    sdtm = SDTM(
        mock_wiki_client,
        mock_library_client,
        mock_sdtm_summary,
        product_type,
        version,
        config,
    )
    mock_wiki_client.get_wiki_table.return_value = mock_dataset_data
    datasets = sdtm.get_datasets()
    dataset_names = [c["fields"]["name"] for c in mock_dataset_data["list"]["entry"]]
    expected_output_keys = ["_links", "name", "ordinal", "label"]
    for dataset in datasets:
        assert dataset.name in dataset_names
        assert (
            dataset.links["self"]["href"]
            == f"/mdr/{product_type}/{version}/datasets/{dataset.name.replace(' ', '')}"
        )
        assert dataset.links.get("parentProduct") == mock_sdtm_summary["_links"]["self"]
        for key in expected_output_keys:
            assert key in dataset.to_json()


@pytest.mark.parametrize("product_type", [("sdtm"), ("sdtmig"), ("sendig")])
def test_get_all_prior_versions(
    mock_wiki_client, mock_library_client, mock_sdtm_summary, product_type
):
    config = Config({})
    version = "5-0"
    sdtm = SDTM(
        mock_wiki_client,
        mock_library_client,
        mock_sdtm_summary,
        product_type,
        version,
        config,
    )
    mock_library_client.get_api_json.side_effect = mock_products_payload
    prior_versions = sdtm._get_all_prior_versions()
    for version in prior_versions:
        assert version["href"].startswith(f"/mdr/{product_type}")


@pytest.mark.parametrize(
    "described_value_domain, expected_output",
    [
        ("(NULLFLAVOR)", "ISO 21090 NullFlavor enumeration"),
        (("NULLFLAVOR"), "ISO 21090 NullFlavor enumeration"),
    ],
)
def test_get_described_value_domain(
    mock_wiki_client,
    mock_library_client,
    mock_sdtm_summary,
    described_value_domain,
    expected_output,
):
    config = Config({})
    version = "5-0"
    sdtm = SDTM(
        mock_wiki_client,
        mock_library_client,
        mock_sdtm_summary,
        "sdtm",
        version,
        config,
    )
    is_described_value_domain = sdtm._isdescribedvaluedomain(described_value_domain)
    assert is_described_value_domain == True
    assert expected_output == sdtm._get_described_value_domain(described_value_domain)

def test_get_qualifiesVariables_links(
    mock_wiki_client,
    mock_library_client,
    mock_sdtm_summary,
    mock_sdtm_variable_data,
):
    config = Config({})
    version = "5-0"
    sdtm = SDTM(
        mock_wiki_client,
        mock_library_client,
        mock_sdtm_summary,
        "sdtm",
        version,
        config,
    )
    variable = Variable(mock_sdtm_variable_data, sdtm)
    variable.parent_class_name = "Findings"
    variable.parent_dataset_name = "test"
    variable.variables_qualified = "var"
    var1 = Variable(mock_sdtm_variable_data, sdtm)
    var2 = Variable(mock_sdtm_variable_data, sdtm)
    var3 = Variable(mock_sdtm_variable_data, sdtm)
    var4 = Variable(mock_sdtm_variable_data, sdtm)
    var1.parent_class_name = "Findings"
    var1.name = "var"
    var2.parent_class_name = "Interventions"
    var2.parent_dataset_name = "test"
    var2.name = "var"
    var3.parent_dataset_name = "test"

    sdtm._add_qualified_variables_link(variable, [var1, var2, var3, var4])
    # only var1 should appear in the qualifiesVariables links because it has the same parent_class
    # var2 should not appear because, though it has the same parent dataset name, its class is in [Interventions, Events, and Findings]
    # none of the other variables should appear because they are not in the list of variables qualified
    assert len(variable.links.get("qualifiesVariables", [])) == 1
