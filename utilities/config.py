import json
import os
from utilities import logger, constants
class Config:
    def __init__(self, config_data):
        self.config_data = config_data
    
    @staticmethod
    def build_from_config_file(file_path):
        with open(file_path) as f:
            data = json.load(f)
        Config.validate_config_data(data)
        return Config(data)
    

    def get(self, key):
        """ Access config data dictionary, if key is not found fallback to environment variables before throwing an error """
        if self.config_data.get(key):
            return self.config_data.get(key)
        if os.environ.get(key):
            return os.environ.get(key)
        else:
            raise KeyError(f"Key {key} does not exist in config data")

    def add(self, key, value):
        """ Add a new key value pair to the config. """
        self.config_data[key] = value

    @staticmethod
    def validate_config_data(data):
        errors = []
        key_to_type_mapping = {
            constants.SUMMARY: str
        }
        for key in key_to_type_mapping:
            if not data.get(key):
                errors.append(f"Expected key {key} does not exist in config data")
            elif not isinstance(data.get(key), key_to_type_mapping.get(key)):
                errors.append(f"Value for key {key} is expected to be of type {key_to_type_mapping.get(key)}")
        if errors:
            for error in errors:
                logger.error(error)
            raise Exception("Config errors found")
