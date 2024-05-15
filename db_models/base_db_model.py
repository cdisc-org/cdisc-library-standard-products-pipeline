from uuid import uuid4
from datetime import datetime
from db_models.cosmos_db_service import CosmosDBService
from abc import abstractmethod
from typing import List

class BaseDBModel:

    def __init__(self, params ={}, db_service=None):
        self.id = params.get("id", str(uuid4()))
        self._db_service = db_service or CosmosDBService.get_instance(
            self._connection_string(),
            self._database_name(),
            self._table_name(),
        )
        self.created_at = params.get("createdAt") or datetime.now().isoformat()
        self.updated_at = params.get("updatedAt") or datetime.now().isoformat()

    @classmethod
    @abstractmethod
    def _connection_string(cls) -> str:
        """
        Returns connection string for each model.
        This method is needed to save a
        model to the corresponding connection string.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _database_name(cls) -> str:
        """
        Returns database name for each model.
        This method is needed to save a
        model to the corresponding database.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _table_name(cls) -> str:
        """
        Returns table name for each model.
        This method is needed to save a
        model to the corresponding table.
        """
        raise NotImplementedError()

    @classmethod
    def query_by_params(
        cls, partition_key: str = None, query_params: dict = None, db_service=None
    ) -> list:
        """
        Gets a list of records from the DB.
        If no params are passed, all records will be returned.
        If partition_key is passed -> it will be added to the query.
        query_params param can be used to filter records.
        query_params example: {"studyId": "CDISC01", "dataBundleId": "test"}
        """
        # avoiding dependency injection here
        db_service = db_service or CosmosDBService.get_instance(
            cls._connection_string(),
            cls._database_name(),
            cls._table_name(),
        )
        db_records: List[dict] = db_service.query_items(
            partition_key=partition_key, query_params=query_params
        )
        return [cls(db_record) for db_record in db_records]

    @classmethod
    def delete(
        cls, id, partition_key: str = None, db_service=None
    ):
        db_service = db_service or CosmosDBService.get_instance(
            cls._connection_string(),
            cls._database_name(),
            cls._table_name(),
        )
        db_service.delete_item(id, partition_key=partition_key)

    def _ensure_valid_record_structure():
        raise NotImplementedError()

    def _save_to_db(self):
        """
        Saves the record to the DB.
        """
        self._ensure_valid_record_structure()
        self._db_service.save_item(self._to_db_dict())
