from bs4 import BeautifulSoup
from markdownify import markdownify
from markdown import markdown
from db_models.ig_document import IGDocument
from uuid import uuid4
from utilities.transformer import Transformer
from utilities.wiki_client import WikiClient
from logging import Logger, getLogger
from utilities.blob_service import BlobService
from utilities import document_tags
from typing import List
import os

class Parser:
    
    def __init__(self, client, logger=None):
        self.client: WikiClient = client
        self.image_blob_service: BlobService = BlobService("images")
        self.logger: Logger = logger or getLogger("wiki-parser")
        self.transformer = Transformer()
    
    def get_markdown(self, url):
        html = self.client.get_html(url)
        return self._get_markdown_from_html(html)
    
    def get_ig_document_tree(self, url, standard, standard_version):
        page_id = self._get_page_id(url)
        children = self._get_page_children(page_id)
        pages = [
            {
                "id": str(uuid4()),
                "title": child["title"],
                "page_data": child
            } for child in children if self._has_children(child["id"])
        ]
        documents = {}
        while pages:
            page = pages.pop()
            title = page.get("title")
            if "specifications" in title.lower() or "content control" in title.lower():
                continue
            page_data = page["page_data"]
            children = self._get_page_children(page_data["id"])
            html = page_data["body"]["view"]["value"]
            markdown_data = self._html_to_markdown(html)
            parsed_html = self._parse_html(html, page_data["id"])
            labels = self._get_labels(page_data["id"])
            tags = self._parse_labels(labels)
            if "specifications" in tags.get("sections", []):
                # Ignore specification tables since they are already in the CDISC library
                continue
            doc_params = {
                "id": page["id"],
                "pageId": page_data["id"],
                "standard": standard,
                "version": standard_version,
                "title": title,
                "html": parsed_html,
                "text": markdown_data,
                "parent": page.get("parent"),
                "parentDocumentTitle": page.get("parentDocumentTitle"),
                "section": next(iter(tags.get("sections", [])), "publication"),
                "structures": tags.get("structures"),
                "useCase": next(iter(tags.get("use_cases", [])), None),
            }

            if tags.get("integrated_standards"):
                doc_params["standard"] = f'{tags["integrated_standards"][0]}ig'
                doc_params["version"] = f"{standard}-{standard_version}"
            document = IGDocument.get_or_create(doc_params)
            new_child_documents = [
                {
                    "id": str(uuid4()),
                    "title": child["title"],
                    "page_data": child,
                    "parent": document.id,
                    "parentDocumentTitle": document.title
                } for child in children
            ]

            for child in new_child_documents:
                document.add_child(child.get("id"), child.get("title"))
            self.logger.debug(f"{document.title} found with children {[child['title'] for child in new_child_documents]}")
            documents[document.id] = document
            pages = pages + new_child_documents
        return documents

    def _parse_labels(self, labels: List[str]) -> dict:
        """
        Returns a dictionary mapping label type to label value
        ex:

        {
            "sections": ["examples"],
            "structures": ["AE", "DM", "TS"],
            "integrated_standards: ["sdtm", "cdash"]
        }
        """
        data = {
            "sections": [],
            "structures": [],
            "integrated_standards": [],
            "use_cases": []
        }
        for label in labels:
            components = label.split("-")
            if len(components) < 2:
                continue
            label_type = components[0]
            if label_type == document_tags.SECTION:
                data["sections"].append(" ".join(components[1:]))
            elif label_type == document_tags.DOMAIN or label_type == document_tags.STRUCTURE:
                data["structures"].append(components[1].upper())
            elif label_type == document_tags.STANDARD:
                data["integrated_standards"].append(components[1])
            elif label_type == document_tags.USE_CASE:
                data["use_cases"].append(" ".join(components[1].split("_")))
        return data

    def _has_children(self, page_id):
        return bool(self._get_page_children(page_id))

    def _html_to_markdown(self, html_data):
        return markdownify(str(html_data), strip=['a'])

    def _parse_html(self, html, page_id) -> str:
        parser = BeautifulSoup(html, 'html.parser')
        for span in parser.find_all("span", {'class': 'jira-issue'}):
            # Remove jira issues in content
            span.decompose()
        for div in parser.find_all("div", {'class':'confluence-information-macro'}):
            div.decompose()
        for div in parser.find_all("div", {'class':'plugin-tabmeta-details'}):
            div.decompose()
        for div in parser.find_all("div", {'class':'expand-control'}):
            # Remove table dropdowns
            div.decompose()
        for img in parser.find_all("img"):
            img_link = img.attrs["src"]
            try:
                data = self.client.download_file(img_link)
                image_path = img_link.split("?")[0]
                image_file_name = f"{page_id}-{image_path.split('/')[-1]}"
                self.image_blob_service.upload_file(data, image_file_name)
                base_url = f"https://cdisclibrary{os.environ.get('ENVIRONMENT', '').lower()}.blob.core.windows.net/images"
                image_link_path = f"{base_url}/{image_file_name}"
                attrs = {
                    "width": img.attrs.get("width", 500),
                    "height": img.attrs.get("height", 500),
                    "src": image_link_path
                }
                img.attrs = attrs
                self.logger.info(f"Successfully duplicated {img_link}")
            except:
                self.logger.error(f"Failed to duplicate {img_link}")
        return self.transformer.get_raw_text(str(parser))
        

    def _get_markdown_from_html(self, html):
        parser = BeautifulSoup(html, 'html.parser')
        data = parser.find("div", {"id": "main-content"})
        return self._html_to_markdown(data)
    
    def _get_page_json(self, url):
        page_id = self._get_page_id(url)
        return self.client.get_wiki_json(page_id)

    def _get_page_id(self, url):
        html = self.client.get_html(url)
        parser = BeautifulSoup(html, 'html.parser')
        data = parser.find("meta", {"name": "ajs-page-id"})
        return data.get("content")
    
    def _get_labels(self, page_id):
        labels_data = self.client.get_page_labels(page_id)
        return [label["name"] for label in labels_data.get("results", [])]
  
    def _get_page_children(self, page_id):
        child_data = self._try_get_child_data(page_id)
        return child_data.get("results")
    
    def _get_title_markdown(self, title):
        return f"{title}\n--------------\n\n"
    
    def _try_get_child_data(self, page_id):
        try:
            return self.client.get_wiki_json(page_id, path="/child/page")
        except:
            return {}
