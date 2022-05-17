import os
import sys
import logging
import azure.functions as func

sys.path.append(os.path.abspath(""))
from product_types.product_factory import ProductFactory
from utilities.config import Config
from utilities import logger
import utilities.constants as constants
from utilities.blob_helper import BlobHelper

def main(config: dict) -> str:
    # setup logging
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logFormatter)
    logger.addHandler(console_handler)

    # get necessary environment variables
    username = os.environ.get(constants.CONFLUENCE_USERNAME)
    password = os.environ.get(constants.CONFLUENCE_PASSWORD)
    api_key = os.environ.get(constants.LIBRARY_API_KEY)

    # generate json
    Config.validate_config_data(config)
    config = Config(config)
    config.add(constants.IGNORE_ERRORS, True) # Ignores spec grabber errors by default
    factory = ProductFactory(username, password, api_key, **{})
    product = factory.build_product(config)
    product_document = product.generate_document()
    product.validate_document(product_document)
    file_name = f"{product_document.get('name', 'untitled').lower().replace(' ', '-').replace('.', '-')}.json" 
    BlobHelper.upload_json(
        product_document=product_document,
        container_name="generated-json",
        blob_name=file_name,
    )
    return file_name
