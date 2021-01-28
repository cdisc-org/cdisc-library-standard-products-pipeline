import json

def compare_sdtm(product, document):
    errors = 0
    href = document["_links"]["self"]["href"]

    data = product.library_client.get_api_json(href)

    document_classes = {}
    data_classes = {}
    for c in document.get("classes"):
        document_classes[c["name"]] = c
    for c in data.get("classes"):
        data_classes[c["name"]] = c

    for key, generated in document_classes.items():
        if generated.get("classVariables"):
            names = set([v["name"] for v in generated.get("classVariables")])
            actual = set([v["name"] for v in data_classes[key].get("classVariables", [])])
            if len(generated.get("classVariables")) != len(data_classes[key].get("classVariables", [])):
                logger.info("Mismatch between generated class variables for {}".format(key))
                logger.info(names - actual)
                errors = errors + 1
        
        if generated.get("datasets"):
            names = set([v["name"] for v in generated.get("datasets")])
            actual = set([v["name"] for v in data_classes[key].get("datasets", [])])
            if len(generated.get("datasets")) != len(data_classes[key].get("datasets", [])):
                logger.info("Mismatch between generated dataset for {}".format(key))
                logger.info(names - actual)
                errors = errors + 1

    document_datasets = {}
    data_datasets = {}
    for c in document.get("datasets"):
        document_datasets[c["name"]] = c
    for c in data.get("datasets"):
        data_datasets[c["name"]] = c

    for key, generated in document_datasets.items():
        if generated.get("datasetVariables"):
            names = set([v["name"] for v in generated.get("datasetVariables")])
            actual = set([v["name"] for v in data_datasets[key].get("datasetVariables", [])])
            if len(generated.get("datasetVariables")) != len(data_datasets[key].get("datasetVariables", [])):
                logger.info("Mismatch between generated dataset variables for {}".format(key))
                logger.info(names - actual)
                errors = errors + 1
    if errors == 0:
        logger.info("No errors found")
    else:
        logger.info("{} errors found".format(errors))

def compare_sendig(product, document):
    errors = 0
    href = document["_links"]["self"]["href"]
    data = product.library_client.get_api_json(href)

    generated_classes = {}
    classes = {}
    datasets = {}
    generated_datasets = {}
    for c in document.get("classes"):
        generated_classes[c["name"]] = c
        for dataset in c.get("datasets", []):
            generated_datasets[dataset["name"]] = dataset
    for c in data.get("classes"):
        classes[c["name"]] = c
        for dataset in c.get("datasets", []):
            datasets[dataset["name"]] = dataset
    
    for key, value in generated_classes.items():
        class_fields_to_compare = ["name", "description", "label", "ordinal"]
        errors = errors + product.compare_fields(classes.get(key, {}),value, class_fields_to_compare)
        for dataset in value.get("datasets", []):
            if datasets.get(dataset["name"]):
                actual_dataset = datasets.get(dataset["name"])
                fields_to_compare = ["name", "label", "description", "datasetStructure", "ordinal"]
                errors = errors + product.compare_fields(actual_dataset, dataset, fields_to_compare)
            else:
                errors = errors + 1
                logger.info("No matching dataset found for {}".format(dataset["name"]))

    if errors == 0:
        logger.info("No errors found")
    else:
        logger.info("{} errors found".format(errors))

def compare_cdash(product, document):
    errors = 0
    href = document["_links"]["self"]["href"]
    data = product.library_client.get_api_json(href)
    document_classes = {}
    data_classes = {}
    for c in document.get("classes"):
        document_classes[c["name"]] = c
    for c in data.get("classes"):
        if c["name"] not in document_classes:
            logger.info("Class {} missing from generated document".format(c["name"]))
            errors = errors + 1
        data_classes[c["name"]] = c

    for key, generated in document_classes.items():
        if generated.get("cdashModelFields"):
            names = set([v["name"] for v in generated.get("cdashModelFields")])
            if key not in data_classes:
                logger.info("Generated class {} does not appear in actual document".format(key))
                errors = errors + 1
            else:
                actual = set([v["name"] for v in data_classes[key].get("cdashModelFields", [])])
                if len(generated.get("cdashModelFields")) != len(data_classes[key].get("cdashModelFields", [])):
                    logger.info("Mismatch between generated class variables for {}".format(key))
                    logger.info(actual - names)
                    logger.info(actual)
                    logger.info(names)
                    errors = errors + 1

    document_domains = {}
    data_domains = {}
    for c in document.get("domains"):
        document_domains[c["name"]] = c
    for c in data.get("domains"):
        if c["name"] not in document_domains:
            logger.info("Domain {} missing from generated document".format(c["name"]))
            errors = errors + 1
        data_domains[c["name"]] = c

    for key, generated_value in document_domains.items():
        if generated_value.get("fields"):
            names = set([v["name"] for v in generated_value.get("fields")])
            if key not in data_domains:
                logger.info("Generated domain {} does not appear in actual data".format(key))
                errors = errors + 1
            else:
                actual = set([v["name"] for v in data_domains[key].get("fields", [])])
                if len(generated.get("fields", [])) != len(data_domains[key].get("fields", [])):
                    logger.info("Mismatch between generated domain fields for {}".format(key))
                    logger.info(actual - names)
                    logger.info(actual)
                    logger.info(names)
                    errors = errors + 1
    if errors == 0:
        logger.info("No errors found")
    else:
        logger.info("{} errors found".format(errors))