import logging
from typing import List
from utilities.wiki_client import WikiClient
from utilities.wiki_document_parser import Parser
from db_models.ig_document import IGDocument
import argparse
from dotenv import load_dotenv
import json

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="Confluence username")
    parser.add_argument("-p", "--password", help="Confluence password")
    parser.add_argument("-t", "--target_url", help="Highest level url of assumptions data", required=True)
    parser.add_argument("-s", "--standard")
    parser.add_argument("-l", "--log_level")
    parser.add_argument("-v", "--version")
    parser.add_argument("-o", "--output", help="Name of the file to write data to. Defaults to assumptions.json", default="data.json")
    args = parser.parse_args()
    return args

def create_logger(args):
    logger = logging.getLogger("load-ig-pipeline")
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    logger.setLevel(args.log_level or logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logFormatter)
    logger.addHandler(console_handler)
    return logger

if __name__ == "__main__":
    args = parse_arguments()
    logger = create_logger(args)
    load_dotenv()
    username = args.username
    password = args.password
    if not username:
        logger.error("Missing required username. Username must be provided as an argument or defined in the environment variable `CONFLUENCE_USERNAME`")
        exit(1)
    if not password:
        logger.error("Missing required password. Password must be provided as an argument or defined in the environment variable `CONFLUENCE_PASSWORD`")
        exit(1)
    client = WikiClient(username, password)
    parser = Parser(client, logger=logger)
    documents: List[IGDocument] = parser.get_ig_document_tree(args.target_url, args.standard, args.version)
    logger.info(f"{len(documents)} documents found.")
    for document in documents.values():
        document._save_to_db()
