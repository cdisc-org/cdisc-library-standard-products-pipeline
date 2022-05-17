from json import dumps
from os import environ
from azure.storage.blob import BlobClient
import utilities.constants as constants


class BlobHelper:
    @staticmethod
    def upload_json(product_document: any, container_name: str, blob_name: str):

        azure_connection_string = environ.get(constants.AZURE_CONNECTION_STRING)
        blob: BlobClient = BlobClient.from_connection_string(
            conn_str=azure_connection_string,
            container_name=container_name,
            blob_name=blob_name,
        )
        blob.upload_blob(
            dumps(product_document, indent=4, sort_keys=True), overwrite=True
        )
