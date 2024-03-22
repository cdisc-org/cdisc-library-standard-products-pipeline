# CDISC Standards Pipeline

Pipeline for generating CDISC library json from the wiki for the following product types:

* SDTM
* SDTMIG
* SEND
* ADAM
* ADAMIG
* CDASH
* CDASHIG

#### Requirements

##### Creating a virtual enviornment

1. Install python 3.9
2. Install virtualenv
   `pip install virtualenv`
3. Create a virtual env
   `python3 -m venv <desired_virtual_env_path>`
4. Activate virtual env
   `<path_to_virtual_env>\Scripts\activate`
5. Install requirements from `requirements.txt`
   `pip install -r requirements.txt`

#### Running the pipeline

##### Setup

The pipeline requires the location of the expected wiki content be defined in 1 of 2 ways. 

ex: https://wiki.cdisc.org/display/~nhaydel/ADaM+OCCDS+1.1+Metadata
Page Information from the ... on the top-right of the page
https://wiki.cdisc.org/pages/viewinfo.action?pageId=118327784

1. Through a config file mapping expected metadata tables to a wiki document id (pageId=):
    ```
    {
        "summary": "11111111",
        "classMetadata": "11111111",
        "domainsMetadata": "11111111",
        "datasetMetadata": "11111111",
        "datastructures": "11111111",
        "variableSets": "11111111",
        "variables": "11111111",
        "scenarioMetadata": "11111111"
    }
   ```
   Note: Some product types only require certain keys to appear in the config. For example SDTM based products only have classes, datasets, and variables so only those values would need to appear in the config when generating the json for that product type. Additionally, the variables specifier is optional. If a variables document is not specified in the config, the pipeline will automatically run the specgrabber for that product.
2. Environment variables defined for each expected metadata table with the value being the associated document id. The environment variable names should match those shown in the config above.

##### Command

###### Arguments

* -c, --config: Specify path to config file
* -u, --username: Confluence username (Can also be stored in the environment variable CONFLUENCE_USERNAME)
* -p, --password: Confluence password (Can also be stored in the environment variable CONFLUENCE_PASSWORD)
* -a, --api_key: CDISC library api key (Can also be stored in the environment variable LIBRARY_API_KEY)
* -r, --report_file: File to log report output. Defaults to report.txt
* -l, --log_level: Log level for all reporting. Options: info, debug, error. Defaults to info
* -i, --ignore_errors: Boolean flag for determining whether or not spec grabber/wiki document errors should stop pipeline execution. These errors will be reported either way.
* -o, --output: Specifies output file

Once the config or environment variables are set up, the pipeline can be run using the following command:

`python .\parse_document.py -u '<confluence_username>' -p '<confluence_password>' -a '<api_key>' -l '<log_level>' -i`

ex: `python .\parse_document.py -c config -l 'info' -i -o log.txt`

##### Tests

Tests can be run by running the following command from the root directory of this repository:

`pytest`

#### Informative Content

To load informative content into the database, for example, for TIG v 1-0:

- Set the env variables (or use the defined command line arguments):

   `CONFLUENCE_USERNAME`
   `CONFLUENCE_PASSWORD`
   `COSMOSDB_ENDPOINT`
   `COSMOSDB_KEY`
   `COSMOSDB_DATABASE_NAME`

- run the command:

   `python load_ig.py -t https://wiki.cdisc.org/display/TATOBA/Tobacco+Implementation+Guide+Home -s tig -v 1-0`
