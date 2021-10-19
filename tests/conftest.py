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
                        "description": "Class description",
                    }
                },
                {
                    "fields": {
                        "name": "Class 2",
                        "label": "Second Class",
                        "ordinal": "2",
                        "description": "Class description",
                    }
                },
            ]
        }
    }


package_list = {
    "_links": {
        "packages": [
            {
                "href": "/mdr/ct/packages/adamct-2014-09-26",
                "title": "ADaM Controlled Terminology Package 19 Effective 2014-09-26",
            },
            {
                "href": "/mdr/ct/packages/adamct-2020-11-06",
                "title": "ADaM Controlled Terminology Package 43 Effective 2020-11-06",
            },
            {
                "href": "/mdr/ct/packages/cdashct-2014-09-26",
                "title": "CDASH Controlled Terminology Package 19 Effective 2014-09-26",
            },
            {
                "href": "/mdr/ct/packages/cdashct-2021-06-25",
                "title": "CDASH Controlled Terminology Package 46 Effective 2021-06-25",
            },
            {
                "href": "/mdr/ct/packages/coact-2014-12-19",
                "title": "COA Controlled Terminology Package 20 Effective 2014-12-19",
            },
            {
                "href": "/mdr/ct/packages/coact-2015-03-27",
                "title": "COA Controlled Terminology Package 21 Effective 2015-03-27",
            },
            {
                "href": "/mdr/ct/packages/define-xmlct-2019-12-20",
                "title": "DEFINE-XML Controlled Terminology Package 40 Effective 2019-12-20",
            },
            {
                "href": "/mdr/ct/packages/define-xmlct-2021-06-25",
                "title": "Define-XML Controlled Terminology Package 46 Effective 2021-06-25",
            },
            {
                "href": "/mdr/ct/packages/glossaryct-2020-12-18",
                "title": "GLOSSARY Controlled Terminology Package 44 Effective 2020-12-18",
            },
            {
                "href": "/mdr/ct/packages/protocolct-2017-03-31",
                "title": "PROTOCOL Controlled Terminology Package 29 Effective 2017-03-31",
            },
            {
                "href": "/mdr/ct/packages/protocolct-2021-06-25",
                "title": "Protocol Controlled Terminology Package 46 Effective 2021-06-25",
            },
            {
                "href": "/mdr/ct/packages/qrsct-2015-06-26",
                "title": "QRS Controlled Terminology Package 22 Effective 2015-06-26",
            },
            {
                "href": "/mdr/ct/packages/qrsct-2015-09-25",
                "title": "QRS Controlled Terminology Package 23 Effective 2015-09-25",
            },
            {
                "href": "/mdr/ct/packages/qs-ftct-2014-09-26",
                "title": "QS-FT Controlled Terminology Package 19 Effective 2014-09-26",
            },
            {
                "href": "/mdr/ct/packages/sdtmct-2014-09-26",
                "title": "SDTM Controlled Terminology Package 19 Effective 2014-09-26",
            },
            {
                "href": "/mdr/ct/packages/sdtmct-2021-06-25",
                "title": "SDTM Controlled Terminology Package 46 Effective 2021-06-25",
            },
            {
                "href": "/mdr/ct/packages/sendct-2014-09-26",
                "title": "SEND Controlled Terminology Package 19 Effective 2014-09-26",
            },
            {
                "href": "/mdr/ct/packages/sendct-2021-06-25",
                "title": "SEND Controlled Terminology Package 46 Effective 2021-06-25",
            },
        ],
        "self": {
            "href": "/mdr/ct/packages",
            "title": "Product Group Terminology",
        },
    }
}

packages = [
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages/sendct-2021-06-25",
                "title": "SEND Controlled Terminology Package 46 Effective 2021-06-25",
            }
        },
        "codelists": [
            {
                "conceptId": "C71113",
                "name": "Frequency",
                "submissionValue": "FREQ",
            },
            {
                "conceptId": "C66742",
                "name": "No Yes Response",
                "submissionValue": "NY",
            },
            {
                "conceptId": "C71148",
                "name": "Position",
                "submissionValue": "POSITION",
            },
        ],
        "name": "SEND CT 2021-06-25",
        "version": "2021-06-25",
    },
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages/sdtmct-2021-06-25",
                "title": "SDTM Controlled Terminology Package 46 Effective 2021-06-25",
            }
        },
        "codelists": [
            {
                "conceptId": "C71113",
                "name": "Frequency",
                "submissionValue": "FREQ",
            },
            {
                "conceptId": "C66742",
                "name": "No Yes Response",
                "submissionValue": "NY",
            },
            {
                "conceptId": "C150811",
                "name": "Other Disposition Event Response",
                "submissionValue": "OTHEVENT",
            },
            {
                "conceptId": "C71148",
                "name": "Position",
                "submissionValue": "POSITION",
            },
            {
                "conceptId": "C114118",
                "name": "Protocol Milestone",
                "submissionValue": "PROTMLST",
            },
        ],
        "name": "SDTM CT 2021-06-25",
        "version": "2021-06-25",
    },
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages/adamct-2020-11-06",
                "title": "ADaM Controlled Terminology Package 43 Effective 2020-11-06",
            }
        },
        "codelists": [],
        "name": "ADaM CT 2020-11-06",
        "version": "2020-11-06",
    },
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages/cdashct-2021-06-25",
                "title": "CDASH Controlled Terminology Package 46 Effective 2021-06-25",
            }
        },
        "codelists": [
            {
                "conceptId": "C78419",
                "name": "Concomitant Medication Dosing Frequency per Interval",
                "submissionValue": "CMDOSFRQ",
            },
            {
                "conceptId": "C78431",
                "name": "Vital Signs Position of Subject",
                "submissionValue": "VSPOS",
            },
        ],
        "name": "CDASH CT 2021-06-25",
        "version": "2021-06-25",
    },
]

product_list = {
    "_links": {
        "data-analysis": {
            "_links": {
                "adam": [
                    {
                        "href": "/mdr/adam/adam-2-1",
                        "title": "Analysis Data Model Version 2.1",
                        "type": "Foundational Model",
                    },
                    {
                        "href": "/mdr/adam/adam-adae-1-0",
                        "title": "Analysis Data Model Data Structure for Adverse Event Analysis Version 1.0",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/adam/adam-occds-1-0",
                        "title": "ADaM Structure for Occurrence Data (OCCDS) Version 1.0",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/adam/adam-tte-1-0",
                        "title": "ADaM Basic Data Structure for Time-to-Event Analyses Version 1.0",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/adam/adamig-1-1",
                        "title": "Analysis Data Model Implementation Guide Version 1.1",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/adam/adamig-1-2",
                        "title": "Analysis Data Model Implementation Guide Version 1.2",
                        "type": "Implementation Guide",
                    },
                ],
                "self": {
                    "href": "/mdr/products/DataAnalysis",
                    "title": "Product Group Data Analysis",
                    "type": "CDISC Library Product Group",
                },
            }
        },
        "data-collection": {
            "_links": {
                "cdash": [
                    {
                        "href": "/mdr/cdash/1-0",
                        "title": "Clinical Data Acquisition Standards Harmonization Model Version 1.0",
                        "type": "Foundational Model",
                    },
                    {
                        "href": "/mdr/cdash/1-1",
                        "title": "Clinical Data Acquisition Standards Harmonization Model Version 1.1",
                        "type": "Foundational Model",
                    },
                ],
                "cdashig": [
                    {
                        "href": "/mdr/cdashig/1-1-1",
                        "title": "Clinical Data Acquisition Standards Harmonization (CDASH) User Guide V1.1",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/cdashig/2-0",
                        "title": "Clinical Data Acquisition Standards Harmonization Implementation Guide for Human Clinical Trials Version 2.0",
                        "type": "Implementation Guide",
                    },
                ],
                "self": {
                    "href": "/mdr/products/DataCollection",
                    "title": "Product Group Data Collection",
                    "type": "CDISC Library Product Group",
                },
            }
        },
        "data-tabulation": {
            "_links": {
                "sdtm": [
                    {
                        "href": "/mdr/sdtm/1-7",
                        "title": "Study Data Tabulation Model Version 1.7",
                        "type": "Foundational Model",
                    },
                    {
                        "href": "/mdr/sdtm/1-8",
                        "title": "Study Data Tabulation Model Version 1.8 (Final)",
                        "type": "Foundational Model",
                    },
                ],
                "sdtmig": [
                    {
                        "href": "/mdr/sdtmig/3-2",
                        "title": "Study Data Tabulation Model Implementation Guide: Human Clinical Trials Version 3.2 (Final)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sdtmig/3-3",
                        "title": "Study Data Tabulation Model Implementation Guide: Human Clinical Trials Version 3.3 (Final)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sdtmig/ap-1-0",
                        "title": "Study Data Tabulation Model Implementation Guide: Associated Persons Version 1.0 (Final)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sdtmig/md-1-0",
                        "title": "SDTM Implementation Guide for Medical Devices SDTMIG-MD 1.0 (Provisional)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sdtmig/md-1-1",
                        "title": "Study Data Tabulation Model Implementation Guide for Medical Devices (SDTMIG-MD) Version 1.1",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sdtmig/pgx-1-0",
                        "title": "Study Data Tabulation Model Implementation Guide: Pharmacogenomics/Genetics Version 1.0 (Provisional)",
                        "type": "Implementation Guide",
                    },
                ],
                "self": {
                    "href": "/mdr/products/DataTabulation",
                    "title": "Product Group Data Tabulation",
                    "type": "CDISC Library Product Group",
                },
                "sendig": [
                    {
                        "href": "/mdr/sendig/3-0",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Nonclinical Studies Version 3.0 (Final)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sendig/3-1",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Nonclinical Studies Version 3.1 (Final)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sendig/ar-1-0",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Animal Rule Version 1.0 (Final)",
                        "type": "Implementation Guide",
                    },
                    {
                        "href": "/mdr/sendig/dart-1-1",
                        "title": "Standard for Exchange of Nonclinical Data Implementation Guide: Developmental and Reproductive Toxicology Version 1.1",
                        "type": "Implementation Guide",
                    },
                ],
            }
        },
        "self": {
            "href": "/mdr/products",
            "title": "CDISC Library Product List",
            "type": "CDISC Library Product List",
        },
    }
}


def mock_products_payload(href):
    if href == "/mdr/ct/packages":
        return package_list
    elif href.startswith("/mdr/ct/packages/"):
        return [
            codelists
            for codelists in packages
            if href == codelists["_links"]["self"]["href"]
        ][0]
    else:
        return product_list


@pytest.fixture()
def mock_adamig_summary():
    return {
        "name": "Test ADAMIG",
        "parentModel": "2-1",
        "_links": {
            "self": {
                "href": "/mdr/adam/adamig-5-0",
                "title": "Test ADAMIG link",
                "type": "Test Implementation Guide",
            }
        },
    }


@pytest.fixture()
def mock_sdtm_summary():
    return {
        "name": "Test SDTM",
        "parentModel": "1-2",
        "_links": {
            "self": {
                "href": "/mdr/sdtm/test",
                "title": "Test SDTM link",
                "type": "Test foundational model",
            }
        },
    }

@pytest.fixture()
def mock_sdtm_variable_data():
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


@pytest.fixture()
def mock_cdash_summary():
    return {
        "name": "Test CDASH",
        "parentModel": "2-1",
        "_links": {
            "self": {
                "href": "/mdr/cdash/5-0",
                "title": "Test CDASH link",
                "type": "Test Foundational Model",
            }
        },
    }
