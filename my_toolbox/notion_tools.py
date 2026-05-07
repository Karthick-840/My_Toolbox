
"""Notion API helpers for database CRUD operations."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


class NotionTools:
    """Utility wrapper around the Notion REST API."""

    def __init__(
        self,
        notion_token: Optional[str] = None,
        database_id: Optional[str] = None,
        notion_version: str = "2024-06-28",
        timeout: int = 30,
    ) -> None:
        self.notion_token = notion_token or os.getenv("NOTION_TOKEN", "")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID", "")
        self.notion_version = notion_version
        self.timeout = timeout

        if not self.notion_token:
            raise ValueError("Notion token is required.")
        if not self.database_id:
            raise ValueError("Notion database ID is required.")

        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": self.notion_version,
        }

    def create_page(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a page in the configured Notion database."""
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_pages(self, num_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read pages from the configured Notion database.

        If num_pages is None, all pages are fetched using pagination.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        get_all = num_pages is None
        page_size = 100 if get_all else num_pages

        payload: Dict[str, Any] = {"page_size": page_size}
        response = requests.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        while data.get("has_more") and get_all:
            payload = {
                "page_size": page_size,
                "start_cursor": data.get("next_cursor"),
            }
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            results.extend(data.get("results", []))

        return results

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Notion page properties payload."""
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"properties": properties}
        response = requests.patch(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def delete_page(self, page_id: str) -> Dict[str, Any]:
        """Archive a Notion page (soft delete)."""
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"archived": True}
        response = requests.patch(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def build_sample_properties(
        title: str,
        description: str,
        published_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a sample properties payload matching URL/Title/Published schema."""
        if published_date is None:
            published_date = datetime.now(timezone.utc).isoformat()

        return {
            "URL": {"title": [{"text": {"content": description}}]},
            "Title": {"rich_text": [{"text": {"content": title}}]},
            "Published": {"date": {"start": published_date, "end": None}},
        }

import requests
import json
import logging
from datetime import datetime, timezone

class NotionTools:
    
    def __init__(self, token, database_id, logger=None):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        
        if logger:
            self.logger = logger
            self.logger.info('Notion Tools Imported.')
        else:
            self.logger = logging.getLogger(__name__)

    def get_pages(self, num_pages=None):
        """
        Retrieves pages from the database. 
        If num_pages is None, it fetches all pages using pagination.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        get_all = num_pages is None
        page_size = 100 if get_all else num_pages

        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=self.headers)
        data = response.json()

        results = data.get("results", [])

        # Pagination logic
        while data.get("has_more") and get_all:
            payload["start_cursor"] = data.get("next_cursor")
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()
            results.extend(data.get("results", []))

        self.logger.info(f"Retrieved {len(results)} pages from Notion.")
        return results

    def modify_pages(self, properties=None, page_id=None):
        """
        Creates, deletes, or updates a page in the database.
        - If page_id is None: Creates a new page.
        - If properties has {'archived': True}: Archives (deletes) the page.
        - Otherwise: Updates the existing page properties.
        """
        # 1. CREATE CASE (No page_id provided)
        if page_id is None:
            url = "https://api.notion.com/v1/pages"
            payload = {
                "parent": {"database_id": self.database_id},
                "properties": properties or {}
            }
            response = requests.post(url, json=payload, headers=self.headers)
            action = "created"

        # 2. DELETE/UPDATE CASE (page_id provided)
        else:
            url = f"https://api.notion.com/v1/pages/{page_id}"
            # If 'archived' is in properties, it's a delete/restore action
            # Otherwise, wrap properties in a 'properties' key for updates
            if properties and "archived" in properties:
                payload = properties
                action = "archived/restored"
            else:
                payload = {"properties": properties or {}}
                action = "updated"
                
            response = requests.patch(url, json=payload, headers=self.headers)

        # Logging and return
        if response.status_code == 200:
            self.logger.info(f"Successfully {action} page.")
        else:
            self.logger.error(f"Error during {action}: {response.text}")
            
        return response.json()

# --- 1. WORKING WITH PAGE CONTENT (BLOCKS) ---
    def get_block_children(self, block_id):
        """Retrieves the children blocks of a specific block/page."""
        url = f"{self.base_url}/blocks/{block_id}/children"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def append_block_children(self, block_id, children_data):
        """Appends new content (blocks) to a page or block."""
        url = f"{self.base_url}/blocks/{block_id}/children"
        payload = {"children": children_data}
        response = requests.patch(url, headers=self.headers, json=payload)
        return response.json()

    # --- 2. WORKING WITH DATABASES ---
    def create_database(self, parent_page_id, title, properties):
        """Creates a new database as a child of a page."""
        url = f"{self.base_url}/databases"
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    # --- 3. DATA SOURCES & SYNC ---
    def create_data_source(self, database_id, title, properties):
        """Adds an external data source to an existing database."""
        url = f"{self.base_url}/data_sources"
        payload = {
            "parent": {"database_id": database_id},
            "title": [{"text": {"content": title}}],
            "properties": properties
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    # --- 4. WORKING WITH COMMENTS ---
    def get_comments(self, block_id):
        """Retrieves comments for a specific block or page."""
        url = f"{self.base_url}/comments?block_id={block_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def create_comment(self, parent_id, comment_text, is_page=True):
        """Creates a comment on a page or in a discussion thread."""
        url = f"{self.base_url}/comments"
        parent_type = "page_id" if is_page else "discussion_id"
        payload = {
            "parent": {parent_type: parent_id},
            "rich_text": [{"text": {"content": comment_text}}]
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    # --- 5. SEARCH ---
    def search(self, query="", filter_obj=None, sort_obj=None):
        """Searches all pages and databases shared with the integration."""
        url = f"{self.base_url}/search"
        payload = {"query": query}
        if filter_obj: payload["filter"] = filter_obj
        if sort_obj: payload["sort"] = sort_obj
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    # --- 6. LINK PREVIEWS (UNFURLING) ---
    def send_link_preview_attribute(self, url, title, description):
        """
        Used for Link Preview integrations to send data to Notion.
        Requires 'Unfurl' capability enabled in Notion settings.
        """
        # This is typically used in response to a web request from Notion
        # when a user pastes a link from your registered domain.
        payload = {
            "unfurl_attribute": {
                "url": url,
                "title": title,
                "description": description
            }
        }
        # Note: This is usually part of a specific 'unfurl' response flow 
        # rather than a standard standalone POST request.
        return payload 
    
# Example Usage:
# properties_example = {
#     "Title": {"title": [{"text": {"content": "New Blog Post"}}]},
#     "URL": {"url": "https://example.com"},
#     "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
# }


# --- Quick Example: Appending a Paragraph to a Page ---
# notion = NotionTools(token="secret_abc123")
# new_block = [{
#     "object": "block",
#     "type": "paragraph",
#     "paragraph": {
#         "rich_text": [{"type": "text", "text": {"content": "Hello from Python!"}}]
#     }
# }]
# notion.append_block_children("your_page_id_here", new_block)


import requests
import logging
from datetime import datetime

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
    
import os
import logging
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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