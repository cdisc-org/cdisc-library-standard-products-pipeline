from product_types.base_product import BaseProduct
from product_types.data_tabulation.variable import Variable
from product_types.data_tabulation.data_tabulation_class import DataTabulationClass
from product_types.data_tabulation.dataset import Dataset
import csv
import sys
from copy import deepcopy
from utilities import logger, constants

class SDTM(BaseProduct):
    def __init__(self, wiki_client, library_client, summary, product_type, version, config):
        super().__init__(wiki_client, library_client, summary, product_type, version, config)
        self.product_category = "data-tabulation"
        self.codelist_types = ["sdtmct"]
        self.is_ig = False
        self.model_type = "sdtm"

    def generate_document(self) -> dict:
        """
        Generate standard product json document
        """
        sdtm_document = deepcopy(self.summary)
        classes, datasets, variables = self.get_metadata()
        sdtm_document["classes"] = [c.to_json() for c in classes]
        sdtm_document["datasets"] = [dataset.to_json() for dataset in datasets]
        sdtm_document = self._cleanup_document(sdtm_document)
        return sdtm_document

    def get_metadata(self, parent: str = None) -> ([dict], [dict], [dict]):
        """
        Gets the classes, datasets, and variables for an sdtm based product.
        Applies appropriate links between variables -> class, variables -> dataset, dataset -> class and class->class

        Arguments:
        parent - link to a parent model where this products classes can be found.

        Returns:
        arrays of classes, datasets and variables
        """
        self.codelist_mapping = self._get_codelist_mapping()
        classes = self.get_classes()
        datasets = self.get_datasets()
        variables = self.get_variables()

        # link variables to appropriate parent structure
        for variable in variables:
            parent_dataset_name = variable.parent_dataset_name.replace("SDTM ", "").replace("SEND ", "")
            parent_class_name = variable.parent_class_name.replace("SDTM ", "").replace("SEND ", "")
            parent_dataset = self._find_dataset(parent_dataset_name, datasets)
            parent_class = self._find_class_by_name(parent_class_name, classes)
            if variable.variables_qualified:
                self._add_qualified_variables_link(variable, variables)
            if self.is_ig:
                if parent_class and parent_class.parent_class_name:
                    variable.build_model_class_variable_link()
                else:
                    variable.build_model_dataset_variable_link()
            if parent_dataset:
                variable.set_parent_dataset(parent_dataset)
                parent_dataset.add_variable(variable)
            elif not self.is_ig and parent_class:
                variable.set_parent_class(parent_class)
                parent_class.add_variable(variable)

        # set up parent class links
        for c in classes:
            parent_class = self._find_class(c.parent_class_name, classes) or self._find_class_by_name(c.parent_class_name, classes)
            if parent_class:
                c.add_link("parentClass", parent_class.links["self"])
                parent_class.links["subclasses"] = parent_class.links.get("subclasses", []) + [c.links["self"]]
        for dataset in datasets:
            parent_class = self._find_class(dataset.parent_class_name, classes) or self._find_class_by_name(dataset.parent_class_name, classes)
            if parent_class:
                dataset.set_parent_class(parent_class)
                parent_class.add_dataset(dataset)
        return classes, datasets, variables

    def validate_document(self, document: dict):
        """
        Validates generated json document
        Arguments:
        document - Json document.
        """
        logger.info("Begin validating")
        for c in document["classes"]:
            self._validate_links(c)
            assert isinstance(c.get("ordinal"), str)
        for d in document["datasets"]:
            self._validate_links(d)
            assert isinstance(d.get("ordinal"), str)
            for variable in d.get("datasetVariables", []):
                assert isinstance(variable.get("ordinal"), str)
                if "parentClass" in variable["_links"]:
                    logger.error(f"Dataset variable found with parent class link: {variable.get('name')}, Parent Dataset: {variable['links'].get('parentDataset')}")
        logger.info("Finished validating")
    
    def get_classes(self) -> [dict]:
        """
        Load classes from wiki

        Returns:

        Array of classes
        """
        document_id = self.config.get(constants.CLASSES)
        classes = []
        classes_data = self.wiki_client.get_wiki_table(document_id, constants.CLASSES)
        class_count = 0
        for record in classes_data["list"]["entry"]:
            class_count = class_count+1
            class_obj = DataTabulationClass(record["fields"], record.get("id"), self)
            if self.is_ig:
                class_obj.set_model_link(self.summary["_links"]["model"]["href"])
            prior_version = self._get_prior_version(class_obj.links["self"])
            if prior_version:
                class_obj.add_link("priorVersion", prior_version)
            class_obj.set_ordinal(str(len(classes) + 1))
            classes.append(class_obj)
        logger.info(f"Finished loading classes: {class_count}/{len(classes_data['list']['entry'])}")
        return classes

    def get_datasets(self) -> [dict]:
        """
        Load datasets from wiki

        Returns:

        Array of datasets
        """
        document_id = self.config.get(constants.DATASETS)
        datasets = []
        datasets_data = self.wiki_client.get_wiki_table(document_id, constants.DATASETS)
        dataset_count = 0
        for record in datasets_data["list"]["entry"]:
            dataset_count = dataset_count+1
            dataset = Dataset(record["fields"], record.get("id"), self)
            if self.is_ig:
                dataset.set_model_link(self.summary["_links"]["model"]["href"])
            prior_version = self._get_prior_version(dataset.links["self"])
            if prior_version:
                dataset.add_link("priorVersion", prior_version)
            dataset.set_ordinal(str(len(datasets) + 1))
            datasets.append(dataset)
        logger.info(f"Finished loading datasets: {dataset_count}/{len(datasets_data['list']['entry'])}")
        return datasets
    
    def get_variables(self) -> [dict]:
        """
        Load variables from wiki

        Returns:
        Array of variables
        """
        try:
            document_id = self.config.get(constants.VARIABLES)
        except KeyError:
            document_id = self.wiki_client.update_spec_grabber_content(self.product_type, self.version)
        variables = []
        json_data = self.wiki_client.get_wiki_json(document_id)
        variables_data = json_data.get("body", {}).get("view", {}).get("value")
        if variables_data:
            reader = self._parse_spec_grabber_output(variables_data)
            for row in reader:
                variable = self._build_variable(row)
                variables.append(variable)
            logger.info("Finished loading variables")
        return variables

    def _build_variable(self, variable_data: dict) -> dict:
        """
        Format variable data from wiki into variable object for the json document

        Arguments:

        variable_data: spec grabber data for a single variable represented as a dictionary

        Returns:

        An SDTM variable
        """
        variable = Variable(variable_data, self)

        variable.set_prior_version()
        return variable
    
    def _find_class(self, class_id: str, classes: DataTabulationClass) -> DataTabulationClass:
        if not class_id:
            return None
        filtered_classes = [c for c in classes if c.id == class_id or c.label == class_id]
        if filtered_classes:
            return filtered_classes[0]
        else:
            logger.error(f"No parent class found with id: {class_id}")
            return None

    def _find_class_by_name(self, class_name: str, classes: DataTabulationClass) -> DataTabulationClass:
        filtered_classes = [c for c in classes if c.name == class_name]
        if filtered_classes:
            return filtered_classes[0]
        else:
            logger.error(f"Unable to find class with name: {class_name}")

    def _find_dataset(self, dataset_name: str, datasets: [Dataset]) -> Dataset:
        if not dataset_name:
            return None
        filtered_datasets = [d for d in datasets if d.name == dataset_name]
        if filtered_datasets:
            return filtered_datasets[0]
        else:
            logger.error(f"No dataset found with name {dataset_name}")
    
    def _add_qualified_variables_link(self, variable: Variable, variables: [Variable]):
        """
        Adds qualifiesVariables link to a variable if another variable is found with the correct name and class

        Arguments:
        variable: variable that qualifies other variables
        variables: list of all other variables.
        """
        variables_qualified_names = set(list(map(lambda x: x.strip(), variable.variables_qualified.split(";"))))
        is_general_observation_class = variable.parent_class_name in ["Findings", "Events", "Interventions"]
        variables_qualified = [v for v in variables if v.name in variables_qualified_names and \
            (
                (v.parent_class_name == variable.parent_class_name and is_general_observation_class) or \
                (v.parent_dataset_name == variable.parent_dataset_name and not is_general_observation_class)
            )]
        if variables_qualified:
            variable.add_link("qualifiesVariables", [v.links["self"] for v in variables_qualified])

        unmatched_variables = variables_qualified_names - set([v.name for v in variables_qualified])
        for var in unmatched_variables:
            logger.error(f"Unable to find qualified variable: {var} for qualifier variable {variable.name}")

    def _cleanup_document(self, document: dict) -> dict:
        """
        Remove unnecessary keys from a json document
        """
        logger.info("Cleaning generated document")
        for c in document.get("classes", []):
            self._cleanup_json(c, ["hasParentClass", "id"])
            for var in c.get("classVariables", []):
                self._cleanup_json(var, ["class", "dataset", "name_no_prefix", "codelist", "qualifiesVariables", "id"])
        for dataset in document.get("datasets", []):
            self._cleanup_json(dataset, ["hasParentContext", "id"])
            for var in dataset.get("datasetVariables", []):
                self._cleanup_json(var, ["class", "dataset", "name_no_prefix", "codelist", "qualifiesVariables", "id"])
        logger.info("Finished cleaning document")
        return document
