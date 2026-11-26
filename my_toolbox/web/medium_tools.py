"""Publish Jupyter notebooks to Medium as draft posts.

    from my_toolbox.web.medium_tools import MediumPublisher
    MediumPublisher().publish_notebook("analysis.ipynb", tags=["python"])  # token: MEDIUM_TOKEN

Notebook parsing needs only the standard library; publishing uses `requests`.
Medium integration tokens: Medium > Settings > Security and apps > Integration tokens.
"""

import base64
import json
import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

API_BASE = "https://api.medium.com/v1"
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif"}


def _text(value) -> str:
    return "".join(value) if isinstance(value, list) else (value or "")


def _fence(body: str, lang: str = "") -> str:
    return f"```{lang}\n{body.rstrip()}\n```"


def load_notebook(path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def notebook_to_markdown(
    notebook: dict,
    image_uploader: Optional[Callable[[bytes, str], str]] = None,
    include_code: bool = True,
    include_outputs: bool = True,
    title: Optional[str] = None,
) -> str:
    """Convert a parsed .ipynb dict to Markdown.

    image_uploader(bytes, mime_type) -> public URL. Without it, image outputs are skipped.
    Cells tagged "remove-cell" are dropped; "remove-input" hides code; "remove-output" hides outputs.
    The first H1 is removed when it matches `title` (Medium shows the title separately).
    """
    language = notebook.get("metadata", {}).get("language_info", {}).get("name", "python")
    blocks: List[str] = []

    for cell in notebook.get("cells", []):
        tags = set(cell.get("metadata", {}).get("tags", []))
        if "remove-cell" in tags:
            continue
        source = _text(cell.get("source")).strip()

        if cell.get("cell_type") == "markdown":
            if source:
                blocks.append(source)
            continue
        if cell.get("cell_type") != "code":
            continue

        if include_code and source and "remove-input" not in tags:
            blocks.append(_fence(source, language))
        if include_outputs and "remove-output" not in tags:
            blocks.extend(_output_blocks(cell.get("outputs", []), image_uploader))

    body = "\n\n".join(blocks)
    if title:
        body = re.sub(rf"\A#\s+{re.escape(title)}\s*\n+", "", body)
    return body


def _output_blocks(outputs, image_uploader) -> List[str]:
    blocks = []
    for out in outputs:
        kind = out.get("output_type")
        if kind == "stream":
            text = _ANSI.sub("", _text(out.get("text")))
            if text.strip():
                blocks.append(_fence(text))
        elif kind in ("execute_result", "display_data"):
            data = out.get("data", {})
            image_mime = next((m for m in _IMAGE_TYPES if m in data), None)
            if image_mime and image_uploader:
                raw = base64.b64decode(_text(data[image_mime]))
                blocks.append(f"![output]({image_uploader(raw, image_mime)})")
            elif "text/plain" in data and not image_mime:
                blocks.append(_fence(_ANSI.sub("", _text(data["text/plain"]))))
        elif kind == "error":
            blocks.append(_fence(f"{out.get('ename', 'Error')}: {out.get('evalue', '')}"))
    return blocks


def notebook_title(notebook: dict, fallback: str = "Untitled") -> str:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "markdown":
            m = re.search(r"^#\s+(.+)$", _text(cell.get("source")), re.M)
            if m:
                return m.group(1).strip()
    return fallback


class MediumPublisher:
    """Thin client for the Medium API (integration token required)."""

    def __init__(self, token: Optional[str] = None, session: Optional[requests.Session] = None,
                 timeout: int = 30):
        self.token = token or os.environ.get("MEDIUM_TOKEN")
        if not self.token:
            raise ValueError("Medium integration token required (argument or MEDIUM_TOKEN env var).")
        self.session = session or requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
        })
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = self.session.request(method, f"{API_BASE}{path}", timeout=self.timeout, **kwargs)
        if not resp.ok:
            raise RuntimeError(f"Medium API {resp.status_code}: {resp.text[:300]}")
        return resp.json()["data"]

    def me(self) -> Dict:
        return self._request("GET", "/me")

    def upload_image(self, data: bytes, mime_type: str = "image/png") -> str:
        ext = _IMAGE_TYPES.get(mime_type, "png")
        return self._request("POST", "/images", files={"image": (f"image.{ext}", data, mime_type)})["url"]

    def create_post(self, title: str, markdown: str, tags: Optional[List[str]] = None,
                    status: str = "draft", publication_id: Optional[str] = None,
                    canonical_url: Optional[str] = None) -> Dict:
        if status not in ("draft", "public", "unlisted"):
            raise ValueError("status must be 'draft', 'public' or 'unlisted'")
        payload = {
            "title": title,
            "contentFormat": "markdown",
            "content": f"# {title}\n\n{markdown}",
            "tags": (tags or [])[:5],
            "publishStatus": status,
        }
        if canonical_url:
            payload["canonicalUrl"] = canonical_url
        path = f"/publications/{publication_id}/posts" if publication_id else f"/users/{self.me()['id']}/posts"
        return self._request("POST", path, json=payload)

    def publish_notebook(self, notebook_path, title: Optional[str] = None,
                         tags: Optional[List[str]] = None, status: str = "draft",
                         publication_id: Optional[str] = None, include_code: bool = True,
                         include_outputs: bool = True, upload_images: bool = True) -> Dict:
        """Convert a notebook and post it to Medium (draft by default); returns the post data."""
        nb = load_notebook(notebook_path)
        title = title or notebook_title(nb, Path(notebook_path).stem)
        markdown = notebook_to_markdown(
            nb,
            image_uploader=self.upload_image if upload_images else None,
            include_code=include_code,
            include_outputs=include_outputs,
            title=title,
        )
        return self.create_post(title, markdown, tags, status, publication_id)
