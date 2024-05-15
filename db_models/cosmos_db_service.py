import logging
from typing import Optional, List, Dict, Any, Union

from azure.core.paging import ItemPaged
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import (
    CosmosResourceExistsError,
    CosmosResourceNotFoundError,
)
from logging import getLogger, Logger


class CosmosDBService:
    """
    This class is a high-level facade over CosmosDB.
    """

    _cosmos_client_instance_map = {}
    _database_instance_map = {}
    _table_name_instance_map = {}

    @classmethod
    def get_instance(cls, connection_string: str, database_name: str, table_name: str):
        instance = cls()
        instance._logger = getLogger("cosmos-db-service")

        instance._connection_string = connection_string
        instance._cosmos_client = cls._cosmos_client_instance_map.get(connection_string)
        if instance._cosmos_client is None:
            instance._cosmos_client = CosmosClient.from_connection_string(
                instance._connection_string
            )
            cls._cosmos_client_instance_map[connection_string] = instance._cosmos_client

        instance._database_name = database_name
        instance._database = cls._database_instance_map.get(
            (connection_string, database_name)
        )
        if instance._database is None:
            instance._database = instance._cosmos_client.get_database_client(
                database=instance._database_name
            )
            cls._database_instance_map[(connection_string, database_name)] = (
                instance._database
            )

        instance._container_name = table_name
        existing_instance = cls._table_name_instance_map.get(
            (connection_string, database_name, table_name)
        )
        if existing_instance is None:
            instance._container = instance._database.get_container_client(
                container=instance._container_name
            )
            cls._table_name_instance_map[(connection_string, database_name, table_name)] = (
                instance
            )
            return instance
        return existing_instance

    def __init__(self):
        self._connection_string: str = None
        self._cosmos_client: CosmosClient = None
        self._database_name: str = None
        self._database: DatabaseProxy = None
        self._container_name: str = None
        self._container: ContainerProxy = None
        self._container_alias: str = "C"
        self._logger: Logger = None

    def save_item(self, item_to_save: dict):
        """
        Saves item to CosmosDb container (table)
        """
        self._logger.info(
            f'Saving item to CosmosDB container "{self._container_name}". item={item_to_save.get("id")}'
        )
        try:
            self._container.create_item(body=item_to_save)
        except CosmosResourceExistsError as e:
            self.update_item(item_to_save)

    def get_item(self, item_id: str, partition_key: str = None) -> Optional[dict]:
        """
        Gets item from CosmosDb container (table) by ID.
        """
        try:
            self._logger.info(
                f'Retrieving item from CosmosDB container "{self._container_name}". item_id={item_id}'
            )
            item: dict = self._container.read_item(
                item=item_id, partition_key=partition_key or item_id
            )
            self._logger.info(f"Retrieved item = {item}")
            return item
        except CosmosResourceNotFoundError:
            self._logger.error(
                f"Item with id={item_id} is not found in CosmosDB table {self._container_name}"
            )
            return None

    def delete_item(self, item_id: Union[Dict[str, Any], str], partition_key: str = None):
        """
        Deletes an item from CosmosDB table.
        """
        partition_key = partition_key or item_id
        self._container.delete_item(item=item_id, partition_key=partition_key)

    def delete_all(self, partition_key: str = None):
        """
        Deletes all items from CosmosDB table.
        """
        for item in self._container.read_all_items():
            partition_key = item[partition_key or "id"]
            self.delete_item(item, partition_key)

    @staticmethod
    def copy_all(
        source_db_service: "CosmosDBService", target_db_service: "CosmosDBService"
    ):
        """
        Copies all items from one CosmosDB table to another.
        """
        for item in source_db_service._container.read_all_items():
            target_db_service._container.create_item(body=item)

    @staticmethod
    def replace_all(
        source_db_service: "CosmosDBService",
        target_db_service: "CosmosDBService",
        partition_key: str = None,
    ):
        """
        Deletes all items from target db and copies all items from source CosmosDB table to target.
        """
        target_db_service.delete_all(partition_key)
        CosmosDBService.copy_all(source_db_service, target_db_service)

    def query_items(
        self, partition_key: str = None, query_params: dict = None
    ) -> List[dict]:
        """
        Queries items with a given partition key or/and parameters.
        If no params are passed, all records will be returned.
        If partition_key is passed -> it will be added to the query.
        If query_params are passed, the query will also have a WHERE statement like:
        "SELECT * FROM Transactions C WHERE C.studyId='CDISC01' AND C.dataBundleId='test'"
        """
        search_params: dict = {
            "query": f"SELECT * FROM {self._container_name} {self._container_alias}",
            "enable_cross_partition_query": True,
        }
        if partition_key:
            search_params["partition_key"] = partition_key
        if query_params and isinstance(query_params, dict):
            search_params["query"] += f" {self._create_where_statement(query_params)}"
        self._logger.info(
            f'Querying items from CosmosDB container "{self._container_name}". search_params={search_params}'
        )
        items_iterator: ItemPaged = self._container.query_items(**search_params)
        items: List[dict] = list(items_iterator)
        self._logger.info(f"items={items}")
        return items

    def update_item(self, item_to_update: dict):
        """
        Updates item in CosmosDb container (table)
        Overwrites the whole document.
        """
        logging.info(f"updating item. update_body={item_to_update}")
        self._container.upsert_item(body=item_to_update)

    def _create_where_statement(self, query_params: dict) -> str:
        conditions: List[str] = []
        for key, value in query_params.items():
            if value is None:
                condition: str = f"NOT IS_DEFINED({self._container_alias}.{key})"
            else:
                condition: str = f"{self._container_alias}.{key}='{value}'"
            conditions.append(condition)
        condition_string: str = " AND ".join(conditions)
        return f"WHERE {condition_string}"
