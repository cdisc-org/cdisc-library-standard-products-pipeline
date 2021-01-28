from product_types.data_tabulation.sdtm import SDTM
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
        sdtm_document["classes"] = classes
        sdtm_document = self._cleanup_document(sdtm_document)
        return sdtm_document
    
    def validate_document(self, document: dict):
        logger.info("Begin validating document")
        self._validate_links(document)
        for c in document["classes"]:
            self._validate_links(c)
            for dataset in c.get("datasets", []):
                self._validate_links(dataset)
        logger.info("Finished validating document")

    def _build_variable(self, variable_data: dict) -> dict:
        variable = super()._build_variable(variable_data)
        codelist = variable.get("codelist", "")
        if self._iscodelist(codelist):
            variable["_links"]["codelist"] = self._get_codelist_links(codelist)
        elif self._isdescribedvaluedomain(codelist):
            variable["describedValueDomain"] = self._get_described_value_domain(codelist)
        elif codelist:
            # The provided codelist is a value list
            variable["valueList"] = [code for code in re.split(r'[\n|;|\\n|,]', codelist)]
        return variable
