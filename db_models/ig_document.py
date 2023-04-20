from db_models.base_db_model import BaseDBModel

class IGDocument(BaseDBModel):

    def __init__(self, params: dict):
        super(IGDocument, self).__init__(params)
        self.standard = params["standard"]
        self.standard_version = params["version"]
        self.title = params["title"]
        self.page_id = params["pageId"]
        self.html = params["html"]
        self.text = params["text"]
        self.parent_document = params.get("parent")
        self.parent_document_title = params.get("parentDocumentTitle")
        self.section = params.get("section")
        self.structures = params.get("structures")
        self.use_case = params.get("useCase")
        self.children = []
        self.children_titles = []
    
    def add_child(self, child: str, title: str):
        self.children.append(child)
        self.children_titles.append(title)

    @classmethod
    def _table_name(cls) -> str:
        """
        Returns table name for the model.
        """
        return "ImplementationGuideDocuments"

    @classmethod
    def get_or_create(cls, record_params={}) -> "IGDocument":
        document = next(iter(cls.query_by_params(
            query_params={
                "standard": record_params.get("standard"),
                "version": record_params.get("version"),
                "pageId": record_params.get("pageId")
            }
        )), None)

        if document:
            document.html = record_params.get("html")
            document.text = record_params.get("text")
            document.parent_document = record_params.get("parent")
            document.parent_document_title = record_params.get("parentDocumentTitle")
            document.section = record_params.get("section")
            document.structures = record_params.get("structures")
            return document
        else:
            return cls(record_params)

    def _ensure_valid_record_structure(self):
        assert self.title and isinstance(self.title, str)
        assert self.id and isinstance(self.id, str)
        assert self.page_id and isinstance(self.page_id, str)
        assert self.standard and isinstance(self.standard, str)
        assert self.standard_version and isinstance(self.standard_version, str)
        if self.parent_document:
            assert isinstance(self.parent_document, str)
            assert self.parent_document_title is not None
            assert isinstance(self.parent_document_title, str)
        if self.section:
            assert isinstance(self.section, str)
        if self.structures:
            assert isinstance(self.structures, list)

    def _to_db_dict(self):
        data = {
            "standard": self.standard,
            "version": self.standard_version,
            "title": self.title,
            "id": self.id,
            "pageId": self.page_id,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "html": self.html,
            "text": self.text,
            "children": self.children,
            "childrenTitles": self.children_titles
        }

        if self.parent_document:
            data["parent"] = self.parent_document
            data["parentDocumentTitle"] = self.parent_document_title
        if self.section:
            data["section"] = self.section
        if self.structures:
            data["structures"] = self.structures
        if self.use_case:
            data["useCase"] = self.use_case
        return data
