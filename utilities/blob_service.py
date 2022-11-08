from json import dumps
from os import environ
from azure.storage.blob import BlobClient
import utilities.constants as constants


class BlobService:

    def __init__(self, container_name: str):
        self.connection_string = environ.get(constants.AZURE_CONNECTION_STRING)
        self.container_name = container_name

    def upload_json(self, product_document: any, blob_name: str):
        blob_client: BlobClient = BlobClient.from_connection_string(
            conn_str=self.connection_string,
            container_name=self.container_name,
            blob_name=blob_name
        )
        blob_client.upload_blob(
            dumps(product_document, indent=4, sort_keys=True), overwrite=True
        )

    def upload_file(self, data, blob_name: str):
        blob_client: BlobClient = BlobClient.from_connection_string(
            conn_str=self.connection_string,
            container_name=self.container_name,
            blob_name=blob_name
        )
        blob_client.upload_blob(
            data, overwrite=True
        )
