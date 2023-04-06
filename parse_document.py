import os
import logging
import argparse
from product_types.product_factory import ProductFactory
from utilities.config import Config
from utilities import logger
import utilities.constants as constants

def setup_logger(args):
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    log_levels = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "error": logging.ERROR
    }
    logger.setLevel(log_levels.get(args.log_level, logging.INFO))
    file_handler = logging.FileHandler(args.report_file, "w")
    file_handler.setFormatter(logFormatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logFormatter)
    logger.addHandler(console_handler)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Config file for metadata locations")
    parser.add_argument("-u", "--username", help="Confluence username")
    parser.add_argument("-p", "--password", help="Confluence password")
    parser.add_argument("-a", "--api_key", help="Library api key")
    parser.add_argument("-r", "--report_file", help="File containing document generation report", default="report.txt")
    parser.add_argument("-l", "--log_level", help="Minimum log level for all logs produced during document parsing.", default="info", choices=["debug", "info", "error"])
    parser.add_argument("-s", "--spec_grabber_doc", help="Doc ID for automated spec grabber output", default="113593236")
    parser.add_argument("-i", "--ignore_errors", help="Include this flag if you'd like to ignore spec grabber errors", action="store_true")
    parser.add_argument("-o", "--output", help="Specifies output file")
    parser.add_argument("-od", "--output_directory", help="Directory to store output files")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_arguments()
    username = args.username or os.environ.get(constants.CONFLUENCE_USERNAME)
    password = args.password or os.environ.get(constants.CONFLUENCE_PASSWORD)
    api_key = args.api_key or os.environ.get(constants.LIBRARY_API_KEY)
    if not username:
        logger.error("Missing required username. Username must be provided as an argument or defined in the environment variable `CONFLUENCE_USERNAME`")
        exit(1)
    if not password:
        logger.error("Missing required password. Password must be provided as an argument or defined in the environment variable `CONFLUENCE_PASSWORD`")
        exit(1)
    if not api_key:
        logger.error("Missing required api_key. API_KEY must be provided as an argument or defined in the environment variable `LIBRARY_API_KEY`")
        exit(1)
    
    setup_logger(args)
    if args.config:
        config = Config.build_from_config_file(args.config)
    else:
        # Creates a blank config. All necessary values should be defined in environment variables if config is not specified
        config = Config({})
    
    config.add(constants.IGNORE_ERRORS, args.ignore_errors)
    arguments = {
        'spec_grabber_doc': args.spec_grabber_doc
    }
    factory = ProductFactory(username, password, api_key, **arguments)
    product = factory.build_product(config)
    if product.product_category == "integrated":
        document_id = config.get(constants.SUMMARY)
        directory = product._get_directory(document_id)
        for entry in directory["list"]["entry"]:
            product_config = Config(product.generate_config(entry))
            product_config.add(constants.IGNORE_ERRORS, args.ignore_errors)
            sub_product = factory.build_product(product_config)
            sub_product.add_integrated_standard_link(product.build_self_link())
            sub_document = sub_product.generate_document()
            sub_product.validate_document(sub_document)
            sub_product.write_document(sub_document, args.output, args.output_directory)
            product.add_standard(sub_product)
    product_document = product.generate_document()
    product.validate_document(product_document)
    product.write_document(product_document, args.output, args.output_directory)
