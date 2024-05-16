import logging
import argparse
from utilities import logger
from db_models.cosmos_db_service import CosmosDBService
from typing import Dict, Any


def setup_logger(args):
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    log_levels = {"info": logging.INFO, "debug": logging.DEBUG, "error": logging.ERROR}
    logger.setLevel(log_levels.get(args.log_level, logging.INFO))
    file_handler = logging.FileHandler(args.report_file, "w")
    file_handler.setFormatter(logFormatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logFormatter)
    logger.addHandler(console_handler)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-cs",
        "--connection_string_source",
        help="COSMOSDB Connection String for Source",
    )
    parser.add_argument(
        "-ds", "--database_source", help="COSMOSDB Database Name for Source"
    )
    parser.add_argument("-ts", "--table_source", help="COSMOSDB Table Name for Source")
    parser.add_argument(
        "-bs", "--blob_source", help="Blob Image Storage Location for Source"
    )
    parser.add_argument(
        "-ct",
        "--connection_string_target",
        help="COSMOSDB Connection String for Target",
    )
    parser.add_argument(
        "-dt", "--database_target", help="COSMOSDB Database Name for Target"
    )
    parser.add_argument("-tt", "--table_target", help="COSMOSDB Table Name for Target")
    parser.add_argument(
        "-bt", "--blob_target", help="Blob Image Storage Location for Target"
    )
    parser.add_argument(
        "-r",
        "--report_file",
        help="File containing document generation report",
        default="report.txt",
    )
    parser.add_argument(
        "-l",
        "--log_level",
        help="Minimum log level for all logs produced during document parsing.",
        default="info",
        choices=["debug", "info", "error"],
    )
    parser.add_argument("-o", "--output", help="Specifies output file")
    parser.add_argument(
        "-od", "--output_directory", help="Directory to store output files"
    )
    args = parser.parse_args()
    return args


def _replace_blob(
    item: Dict[str, Any], blob_source: str, blob_target: str
) -> Dict[str, Any]:
    item["html"] = item["html"].replace(blob_source, blob_target)
    return item


if __name__ == "__main__":
    args = parse_arguments()
    setup_logger(args)
    source_db = CosmosDBService.get_instance(
        args.connection_string_source,
        args.database_source,
        args.table_source,
    )
    target_db = CosmosDBService.get_instance(
        args.connection_string_target,
        args.database_target,
        args.table_target,
    )
    CosmosDBService.replace_all(
        source_db,
        target_db,
        transformation=lambda item: _replace_blob(
            item, args.blob_source, args.blob_target
        ),
    )
