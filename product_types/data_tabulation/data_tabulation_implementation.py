
from product_types.data_tabulation.sdtm import SDTM
from product_types.data_tabulation.variable import Variable
from copy import deepcopy
from utilities import logger
import re

class DataTabulationImplementation(SDTM):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config = None):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.model_type = "sdtm"
        self.parent_model = None # defined when parsing the document`
        self.is_ig = True
    
    def generate_document(self) -> dict:
        self.summary["_links"]["model"] = self._build_model_link()
        sdtm_document = deepcopy(self.summary)
        classes, datasets, variables = self.get_metadata()
        sdtm_document["classes"] = [c.to_json() for c in classes]
        sdtm_document = self._cleanup_document(sdtm_document)
        return sdtm_document
    
    def validate_document(self, document: dict):
        logger.info("Begin validating document")
        self._validate_links(document)
        for c in document["classes"]:
            assert isinstance(c.get("ordinal"), str)
            self._validate_links(c)
            for dataset in c.get("datasets", []):
                assert isinstance(dataset.get("ordinal"), str)
                self._validate_links(dataset)
        logger.info("Finished validating document")

    def _build_variable(self, variable_data: dict) -> dict:
        variable: Variable = super()._build_variable(variable_data)
        if self._iscodelist(variable.codelist) and variable.codelist != "N/A":
            codelist_submission_values = self.parse_codelist_submission_values(variable.codelist)
            variable.add_codelist_links(codelist_submission_values)
            variable.add_codelist_submission_values(codelist_submission_values)
        elif self._isdescribedvaluedomain(variable.codelist) and variable.codelist != "N/A":
            variable.set_described_value_domain(variable.codelist)
        elif variable.codelist and variable.codelist != "N/A":
            # The provided codelist is a value list
            variable.set_value_list(variable.codelist)
        return variable

    def _cleanup_document(self, document: dict) -> dict:
        """
        Remove unnecessary keys from a json document
        """
        logger.info("Cleaning generated document")
        for c in document.get("classes", []):
            self._cleanup_json(c, ["hasParentClass", "id"])
            for dataset in c.get("datasets", []):
                self._cleanup_json(dataset, ["hasParentContext", "id"])
                for var in dataset.get("datasetVariables", []):
                    self._cleanup_json(var, ["class", "dataset", "name_no_prefix", "codelist", "qualifiesVariables", "id"])
        logger.info("Finished cleaning document")
        return document
