from product_types.data_tabulation.data_tabulation_implementation import DataTabulationImplementation
class SDTMIG(DataTabulationImplementation):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config = None):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.codelist_types = ["sdtmct"]