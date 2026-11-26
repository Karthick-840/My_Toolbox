
"""Notion API helpers for database CRUD operations."""

import logging
import os
from typing import Any, Dict, List, Optional

import requests


class NotionTools:
    def __init__(self, token, database_id=None, logger=None):
        self.token = token
        # database_id often acts as the default parent for new data sources
        self.database_id = database_id 
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28", # Use 2025-09-03 for Data Source features
        }
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info('Notion Tools Initialized.')

    # --- 1. UNIFIED PAGE & CONTENT MODIFIER ---
    def modify_object(self, obj_type, obj_id=None, properties=None, children=None, parent_id=None):
        """
        Merged function for Pages and Blocks.
        - obj_type: 'pages' or 'blocks'
        - obj_id: ID of the page/block to update/delete. If None (and pages), creates new.
        - properties: Property dictionary (for pages). Use {'archived': True} to delete.
        - children: List of block objects (for page content or block children).
        """
        # CREATE PAGE
        if obj_type == 'pages' and not obj_id:
            url = f"{self.base_url}/pages"
            # In new API, pages are often parented by data_source_id
            parent_type = "database_id" if self.database_id else "page_id"
            payload = {
                "parent": {parent_type: parent_id or self.database_id},
                "properties": properties or {},
                "children": children or []
            }
            response = requests.post(url, json=payload, headers=self.headers)
            return self._handle_response(response, "created page")

        # UPDATE/DELETE PAGE OR APPEND BLOCKS
        endpoint = "pages" if obj_type == 'pages' else "blocks"
        url = f"{self.base_url}/{endpoint}/{obj_id}"
        
        if obj_type == 'pages':
            # Patch for properties or archiving
            payload = properties if properties and "archived" in properties else {"properties": properties}
            response = requests.patch(url, json=payload, headers=self.headers)
        else:
            # For blocks: if children provided, we use the append endpoint
            if children:
                url = f"{url}/children"
                payload = {"children": children}
                response = requests.patch(url, json=payload, headers=self.headers)
            else:
                response = requests.get(url, headers=self.headers) # Retrieval case

        return self._handle_response(response, f"modified {obj_type}")

    # --- 2. UNIFIED DATABASE & DATA SOURCE MANAGER ---
    def manage_data_structure(self, action, target_id=None, title=None, properties=None):
        """
        Merged function for Databases and Data Sources.
        - action: 'create_db', 'create_source', 'query', 'search'
        """
        if action == 'search':
            url = f"{self.base_url}/search"
            payload = {"query": title or ""}
            response = requests.post(url, json=payload, headers=self.headers)
            return self._handle_response(response, "search")

        if action == 'query':
            # New API allows querying either a database or a data_source
            url = f"{self.base_url}/data_sources/{target_id}/query"
            response = requests.post(url, json={"page_size": 100}, headers=self.headers)
            return self._handle_response(response, "query")

        # Create Logic
        url = f"{self.base_url}/databases" if action == 'create_db' else f"{self.base_url}/data_sources"
        payload = {
            "title": [{"text": {"content": title}}] if title else [],
            "properties": properties or {}
        }
        if action == 'create_db':
            payload["parent"] = {"type": "page_id", "page_id": target_id}
        else:
            payload["parent"] = {"database_id": target_id or self.database_id}
            
        response = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(response, action)

    # --- 3. UNIFIED ENGAGEMENT (COMMENTS & PREVIEWS) ---
    def interact(self, block_id, text=None, preview_data=None):
        """Merged function for Comments and Link Previews."""
        if preview_data:
            return {"unfurl_attribute": preview_data} # Helper for Link Previews

        url = f"{self.base_url}/comments"
        if text: # POST comment
            payload = {"parent": {"page_id": block_id}, "rich_text": [{"text": {"content": text}}]}
            response = requests.post(url, json=payload, headers=self.headers)
        else: # GET comments
            url = f"{url}?block_id={block_id}"
            response = requests.get(url, headers=self.headers)
            
        return self._handle_response(response, "interaction")

    def _handle_response(self, response, action_name):
        if response.status_code in [200, 201]:
            self.logger.info(f"Success: {action_name}")
            return response.json()
        self.logger.error(f"Error {action_name}: {response.status_code} - {response.text}")
        return response.json()
    

class NotionMaster:
    """
    A comprehensive Notion API wrapper combining Database CRUD, 
    Block Manipulation, Comments, and Search.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        database_id: Optional[str] = None,
        notion_version: str = "2022-06-28", # Stable version for core features
        logger: Optional[logging.Logger] = None
    ) -> None:
        self.token = token or os.getenv("NOTION_TOKEN", "")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID", "")
        self.base_url = "https://api.notion.com/v1"
        self.logger = logger or logging.getLogger(__name__)

        if not self.token:
            raise ValueError("Notion token is required.")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": notion_version,
        }
        self.logger.info("Notion Master Tool Initialized.")

    # --- 1. DATABASE & PAGE OPERATIONS ---

    def query_database(self, num_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch pages from the database with automatic pagination."""
        url = f"{self.base_url}/databases/{self.database_id}/query"
        results = []
        payload = {"page_size": 100}
        has_more = True
        
        while has_more:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()
            results.extend(data.get("results", []))
            
            has_more = data.get("has_more", False)
            if num_pages and len(results) >= num_pages:
                return results[:num_pages]
            
            payload["start_cursor"] = data.get("next_cursor")
        
        return results

    def create_page(self, properties: Dict[str, Any], children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Creates a new page in the database with optional content (children blocks)."""
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        if children:
            payload["children"] = children
            
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update properties of an existing page."""
        url = f"{self.base_url}/pages/{page_id}"
        payload = {"properties": properties}
        response = requests.patch(url, json=payload, headers=self.headers)
        return response.json()

    def delete_page(self, page_id: str) -> Dict[str, Any]:
        """Archives a page (Notion's version of delete)."""
        url = f"{self.base_url}/pages/{page_id}"
        response = requests.patch(url, json={"archived": True}, headers=self.headers)
        return response.json()

    # --- 2. BLOCK & CONTENT OPERATIONS ---

    def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """Retrieves content blocks from a page or parent block."""
        url = f"{self.base_url}/blocks/{block_id}/children"
        response = requests.get(url, headers=self.headers)
        return response.json().get("results", [])

    def append_content(self, block_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Appends new blocks (paragraphs, images, etc) to a page."""
        url = f"{self.base_url}/blocks/{block_id}/children"
        payload = {"children": blocks}
        response = requests.patch(url, json=payload, headers=self.headers)
        return response.json()

    # --- 3. ENGAGEMENT (COMMENTS & SEARCH) ---

    def add_comment(self, page_id: str, text: str) -> Dict[str, Any]:
        """Adds a comment to a specific page."""
        url = f"{self.base_url}/comments"
        payload = {
            "parent": {"page_id": page_id},
            "rich_text": [{"text": {"content": text}}]
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def search(self, query: str = "") -> List[Dict[str, Any]]:
        """Search across all workspaces the integration has access to."""
        url = f"{self.base_url}/search"
        payload = {"query": query}
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json().get("results", [])

    # --- 4. UTILITIES ---

    @staticmethod
    def build_simple_property(title_text: str) -> Dict[str, Any]:
        """Helper to build a standard 'Name' or 'Title' property."""
        return {"title": [{"text": {"content": title_text}}]}