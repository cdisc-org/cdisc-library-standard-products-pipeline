from product_types.base_product import BaseProduct
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
        self.expected_class_fields = set(["name", "label", "description", "ordinal", "hasParentClass", "ccode", "classStructure"])
        self.expected_dataset_fields = set(["name", "label", "description", "ordinal", "datasetStructure", "hasParentContext", "ccode"])
        self.model_type = "sdtm"
        self.dataset_name_mappings = {
            "SUPP--": "SUPPQUAL",
            "SUPP": "SUPPQUAL"
        }

    def generate_document(self) -> dict:
        """
        Generate standard product json document
        """
        sdtm_document = deepcopy(self.summary)
        classes, datasets, variables = self.get_metadata()
        sdtm_document["classes"] = classes
        sdtm_document["datasets"] = datasets
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
        if parent:
            classes = self.get_classes_from_parent(parent)
        else:
            classes = self.get_classes()
        datasets = self.get_datasets()
        variables = self.get_variables()

        # link variables to appropriate parent structure
        for variable in variables:
            if self.has_parent_model:
                self._build_model_variable_link(variable, classes)
            if variable.get("dataset"):
                self._add_variable_to_dataset(variable, variable.get("dataset"), datasets)
            else:
                self._add_variable_to_class(variable, variable.get("class"), classes)
            self._cleanup_json(variable, ["class", "dataset", "name_no_prefix", "codelist"])

        # set up parent class links
        for c in classes:
            if c.get("hasParentClass"):
                self._assign_parent_class(c, classes)
        for dataset in datasets:
            if dataset.get("hasParentContext"):
                self._add_dataset_to_class(dataset, classes)
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
        for d in document["datasets"]:
            self._validate_links(d)
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
            data = self._build_object(record["fields"], self.expected_class_fields, "classes")
            data["id"] = record.get("id")
            classes.append(data)
        logger.info(f"Finished loading classes: {class_count}/{len(classes_data['list']['entry'])}")
        return classes
    
    def get_classes_from_parent(self, parent_link: str) -> [dict]:
        """
        Load classes from parent model.

        Arguments:

        parent_link: href link to parent model

        Returns:

        Array of classes
        """
        data = self.library_client.get_api_json(parent_link)
        classes = data.get("classes")
        new_classes = []
        for c in classes:
            new_class = self._build_object(c, self.expected_class_fields, "classes")
            if c["_links"].get("parentClass"):
                new_class["hasParentClass"] = c["_links"].get("parentClass")["title"]
            new_classes.append(new_class)
        
        logger.info(f"Retrieved {len(new_classes)} classes from parent {parent_link}")
        return new_classes
        

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
            dataset = self._build_object(record["fields"], self.expected_dataset_fields, "datasets")
            dataset["id"] = record.get("id")
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
        variable = {
            "name": variable_data.get("Variable Name", ""),
            "name_no_prefix": variable_data.get("Variable Name (no prefix)"),
            "label": variable_data.get("Variable Label"),
            "simpleDatatype": variable_data.get("Type"),
            "ordinal": str(variable_data.get("Seq. for Order", "-1")),
            "role": variable_data.get("Role"),
            "description": self.transformer.cleanup_html_encoding(variable_data.get("Description", variable_data.get("CDISC Notes", ""))),
            "core": variable_data.get("Core"),
            "dataset": self.dataset_name_mappings.get(variable_data.get("Dataset Name", ""), variable_data.get("Dataset Name", "")),
            "class": self.class_name_mappings.get(variable_data["Observation Class"], variable_data["Observation Class"]),
            "codelist": variable_data.get("Controlled Terms, Codelist, or Format", "")
        }

        if not self.is_ig:
            variable["roleDescription"]: variable_data.get("Role")
        variable["_links"] = self.__build_variable_links(variable)
        return variable
    
    def _build_object(self, record: dict, expected_fields: [str], category: str) -> dict:
        """
        Build either a class or dataset given a wiki confiforms table record.

        Arguments:

        record: Dictionary of metadata sourced from confiforms table in the wiki
        expected_fields: Fields we expect to store in the resulting json
        category: Either classes or datasets, determines which object to build

        Returns:
        A class or dataset
        """
        data = {}
        key_type_conversions = {
            "ordinal": str
        }
        for key in record:
            if key in expected_fields:
                value_type = key_type_conversions.get(key, str)
                if key == "name" and category == "datasets":
                    value = self.dataset_name_mappings.get(record[key], record[key])
                elif key == "name" and category == "classes":
                    value = self.class_name_mappings.get(record[key], record[key])
                else:
                    value = record[key]
                data[key] = value_type(value)
        data["_links"] = self.__build_object_links(data, category)
        return data

    def __build_variable_links(self, variable: dict) -> dict:
        """ Build the value for the links key of an sdtm variable """
        variable_type = "datasets" if variable.get("dataset") else "classes"
        if variable_type == "datasets":
            parent_name = variable.get("dataset")
        else:
            parent_name = self.transformer.format_name_for_link(variable.get("class"))
        type_label = "SDTM Class Variable" if variable_type == "classes" else "SDTM Dataset Variable"
        links = {
            "self": {
                "href": f"/mdr/{self.product_type}/{self.version}/{variable_type}/{parent_name}/variables/{variable['name']}",
                "title": variable["label"],
                "type": type_label
            },
            "rootItem": {
                "href": f"/mdr/root/{self.product_type}/{variable_type}/{parent_name}/variables/{variable['name']}",
                "title": f"Version-agnostic anchor resource for {self.product_type.upper()} variable {parent_name}.{variable['name']}",
                "type": "Root Data Element"
            }
        }
        links["parentProduct"] = self.summary["_links"]["self"]
        prior_version = self._get_variable_prior_version(links["rootItem"])
        if prior_version:
            links["priorVersion"] = prior_version
        return links

    def __build_object_links(self, data: dict, category: str) -> dict:
        """ Build the value for the links key of a higher level sdtm object (class or dataset) """
        links = {}
        name = self.transformer.format_name_for_link(data["name"])
        type_label = "Class" if category == "classes" else f"SDTM Dataset"
        self_link = {
            "href": f"/mdr/{self.product_type}/{self.version}/{category}/{name}",
            "title": data.get("label"),
            "type": type_label
        }
        if self.summary["_links"].get("model"):
            try:
                model_href = self.summary["_links"]["model"]["href"] + f"/{category}/{name}"
                self.library_client.get_api_json(model_href)
                model_link = {
                        "href": self.summary["_links"]["model"]["href"] + f"/{category}/{name}",
                        "title": data["label"],
                        "type": type_label
                    }
                if category == "classes":
                    links["modelClass"] = model_link
                else:
                    links["modelDataset"] = model_link
            except:
                pass
        links["self"] = self_link
        links["parentProduct"] = self.summary["_links"]["self"]
        prior_version = self._get_prior_version(self_link)
        if prior_version:
            links["priorVersion"] = prior_version
        return links
    
    def _add_variable_to_class(self, variable: dict, class_name: str, classes: [dict]):
        """ Adds a variable to a class's classVariables array and creates the parentClass link for the variable """
        filtered_classes = [c for c in classes if c["name"] == class_name]
        if filtered_classes:
            parent = filtered_classes[0]
            variable["_links"]["parentClass"] = parent["_links"]["self"]
            parent["classVariables"] = parent.get("classVariables", []) + [variable]
        else:
            logger.error(f"Unable to add variable {variable['name']} to class {class_name}")

    def _add_variable_to_dataset(self, variable: dict, dataset_name: str, datasets: [dict]):
        """ Adds a variable to a dataset's datasetVariables array and creates the parent dataset link for the variable """
        filtered_datasets = [d for d in datasets if d["name"] == dataset_name]
        if filtered_datasets:
            parent = filtered_datasets[0]
            variable["_links"]["parentDataset"] = parent["_links"]["self"]
            parent["datasetVariables"] = parent.get("datasetVariables", []) + [variable]
        else:
            logger.error(f"Unable to add variable {variable['name']} to dataset {dataset_name}")

    def _assign_parent_class(self, class_data: dict, classes: [dict]):
        """
        Adds a class with a known parent class to the parent classes list of subclasses. This function will also create the parent class link within the subclass
        """
        parent_class = class_data.get("hasParentClass")
        # Filter by id or label matching parent class because if classes were pulled from a parent model they will not have an id.
        # Classes are pulled from a parent model for implementation guides
        filtered_classes = [c for c in classes if c.get("id") == parent_class or c.get("label") == parent_class]
        if filtered_classes:
            parent = filtered_classes[0]
            class_data["_links"]["parentClass"] = parent["_links"]["self"]
            parent["_links"]["subclasses"] = parent["_links"].get("subclasses", []) + [class_data["_links"]["self"]]
        else:
            logger.error(f"No parent class found with id: {class_data.get('hasParentClass')}")
    
    def _add_dataset_to_class(self, dataset: dict, classes: [dict]):
        """
        Adds a dataset with a known parent class to the parent class
        """
        parent_class = dataset.get("hasParentContext")
        # Filter by id or label matching parent class because if classes were pulled from a parent model they will not have an id.
        # Classes are pulled from a parent model for implementation guides
        filtered_classes = [c for c in classes if c.get("id") == parent_class or c.get("label") == parent_class]
        for filtered_class in filtered_classes:
            dataset["_links"]["parentClass"] = filtered_class["_links"]["self"]
            if self.is_ig:
                filtered_class["datasets"] = filtered_class.get("datasets", []) +  [dataset]
        if not filtered_classes:
            logger.error(f"No parent class found with id: {dataset['hasParentContext']}")

    def _class_variable(self, variable: dict, classes: [dict]) -> bool:
        class_name = variable["class"]
        matching_class = [c for c in classes if c["name"] == class_name]
        if matching_class:
            match = matching_class[0]
            return match.get("hasParentClass") is not None
        return False

    def _build_model_variable_link(self, variable: dict, classes: [dict]):
        """
        Generates the link to a model variable in the case that the sdtm based product is an ig.

        Arguments:

        variable: variable json
        classes: all classes for the current product
        """
        model_variable_key = "modelClassVariable" if self._class_variable(variable, classes) else "modelDatasetVariable"
        model_variable_type = "classes" if model_variable_key == "modelClassVariable" else "datasets"
        model_variable_parent = variable.get('class') if model_variable_key == "modelClassVariable" else variable.get("dataset")
        parent_model_name = self.transformer.replace_str(str(self.parent_model), '.', '-')
        class_variable_name =  variable['name'] if variable["name"] == variable["name_no_prefix"] else "--" + variable["name_no_prefix"]
        variable_name = variable['name'] if model_variable_key == "modelDatasetVariable" else class_variable_name
        model_link_href = f"/mdr/{self.model_type}/{parent_model_name}/{model_variable_type}/{model_variable_parent}/variables/{variable_name}"
        try:
            data = self.library_client.get_api_json(model_link_href)
            variable["_links"][model_variable_key] = data["_links"]["self"]
        except:
            model_link_href = f"/mdr/{self.model_type}/{parent_model_name}/{model_variable_type}/GeneralObservations/variables/{variable_name}"
            try:
                data = self.library_client.get_api_json(model_link_href)
                variable["_links"][model_variable_key] = data["_links"]["self"]
            except:
                pass
    
    def _cleanup_document(self, document: dict) -> dict:
        """
        Remove unnecessary keys from a json document
        """
        logger.info("Cleaning generated document")
        for c in document.get("classes", []):
            self._cleanup_json(c, ["hasParentClass", "id"])
            for dataset in c.get("datasets", []):
                self._cleanup_json(dataset, ["hasParentContext", "id"])
        for dataset in document.get("datasets", []):
            self._cleanup_json(dataset, ["hasParentContext", "id"])
        logger.info("Finished cleaning document")
        return document