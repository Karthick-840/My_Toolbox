
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