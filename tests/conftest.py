import pytest
from unittest import mock
from utilities.wiki_client import WikiClient
from utilities.library_client import LibraryClient

@pytest.fixture()
def mock_wiki_client():
    return mock.Mock(spec=WikiClient)

@pytest.fixture()
def mock_library_client():
    return mock.Mock(spec=LibraryClient)

@pytest.fixture()
def mock_classes_data():
    return {
        "list": {
            "entry": [
                {
                    "fields": {
                        "name": "Class 1",
                        "label": "First Class",
                        "ordinal": "1",
                        "description": "Class description"
                    }
                },
                {
                    "fields": {
                        "name": "Class 2",
                        "label": "Second Class",
                        "ordinal": "2",
                        "description": "Class description"
                    }
                }
            ]
        }
    }

@pytest.fixture()
def mock_products_payload():
    return {
    "_links": {
        "data-analysis": {
            "_links": {
                "adam": [
                    {
                        "href": "/mdr/adam/adam-2-1",
                        "title": "Analysis Data Model Version 2.1",
                        "type": "Foundational Model"
                    },
                    {
                        "href": "/mdr/adam/adam-adae-1-0",
                        "title": "Analysis Data Model Data Structure for Adverse Event Analysis Version 1.0",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/adam/adam-occds-1-0",
                        "title": "ADaM Structure for Occurrence Data (OCCDS) Version 1.0",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/adam/adam-tte-1-0",
                        "title": "ADaM Basic Data Structure for Time-to-Event Analyses Version 1.0",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/adam/adamig-1-1",
                        "title": "Analysis Data Model Implementation Guide Version 1.1",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/adam/adamig-1-2",
                        "title": "Analysis Data Model Implementation Guide Version 1.2",
                        "type": "Implementation Guide"
                    }
                ],
                "self": {
                    "href": "/mdr/products/DataAnalysis",
                    "title": "Product Group Data Analysis",
                    "type": "CDISC Library Product Group"
                }
            }
        },
        "data-collection": {
            "_links": {
                "cdash": [
                    {
                        "href": "/mdr/cdash/1-0",
                        "title": "Clinical Data Acquisition Standards Harmonization Model Version 1.0",
                        "type": "Foundational Model"
                    },
                    {
                        "href": "/mdr/cdash/1-1",
                        "title": "Clinical Data Acquisition Standards Harmonization Model Version 1.1",
                        "type": "Foundational Model"
                    }
                ],
                "cdashig": [
                    {
                        "href": "/mdr/cdashig/1-1-1",
                        "title": "Clinical Data Acquisition Standards Harmonization (CDASH) User Guide V1.1",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/cdashig/2-0",
                        "title": "Clinical Data Acquisition Standards Harmonization Implementation Guide for Human Clinical Trials Version 2.0",
                        "type": "Implementation Guide"
                    }
                ],
                "self": {
                    "href": "/mdr/products/DataCollection",
                    "title": "Product Group Data Collection",
                    "type": "CDISC Library Product Group"
                }
            }
        },
        "data-tabulation": {
            "_links": {
                "sdtm": [
                    {
                        "href": "/mdr/sdtm/1-7",
                        "title": "Study Data Tabulation Model Version 1.7",
                        "type": "Foundational Model"
                    },
                    {
                        "href": "/mdr/sdtm/1-8",
                        "title": "Study Data Tabulation Model Version 1.8 (Final)",
                        "type": "Foundational Model"
                    }
                ],
                "sdtmig": [
                    {
                        "href": "/mdr/sdtmig/3-2",
                        "title": "Study Data Tabulation Model Implementation Guide: Human Clinical Trials Version 3.2 (Final)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sdtmig/3-3",
                        "title": "Study Data Tabulation Model Implementation Guide: Human Clinical Trials Version 3.3 (Final)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sdtmig/ap-1-0",
                        "title": "Study Data Tabulation Model Implementation Guide: Associated Persons Version 1.0 (Final)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sdtmig/md-1-0",
                        "title": "SDTM Implementation Guide for Medical Devices SDTMIG-MD 1.0 (Provisional)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sdtmig/md-1-1",
                        "title": "Study Data Tabulation Model Implementation Guide for Medical Devices (SDTMIG-MD) Version 1.1",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sdtmig/pgx-1-0",
                        "title": "Study Data Tabulation Model Implementation Guide: Pharmacogenomics/Genetics Version 1.0 (Provisional)",
                        "type": "Implementation Guide"
                    }
                ],
                "self": {
                    "href": "/mdr/products/DataTabulation",
                    "title": "Product Group Data Tabulation",
                    "type": "CDISC Library Product Group"
                },
                "sendig": [
                    {
                        "href": "/mdr/sendig/3-0",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Nonclinical Studies Version 3.0 (Final)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sendig/3-1",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Nonclinical Studies Version 3.1 (Final)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sendig/ar-1-0",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Animal Rule Version 1.0 (Final)",
                        "type": "Implementation Guide"
                    },
                    {
                        "href": "/mdr/sendig/dart-1-1",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Developmental and Reproductive Toxicology Version 1.1",
                        "type": "Implementation Guide"
                    }
                ]
            }
        },
        "self": {
            "href": "/mdr/products",
            "title": "CDISC Library Product List",
            "type": "CDISC Library Product List"
        }
    }
}