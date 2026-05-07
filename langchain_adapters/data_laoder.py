"""Unified document loader for unstructured data.

Supported sources
-----------------
.pdf        PyPDFLoader (page-level) or UnstructuredPDFLoader (layout-aware)
.csv        CSVLoader  — each row becomes a document
.txt / .md  TextLoader
.docx       Docx2txtLoader
.json       JSONLoader (pass jq_schema to choose which field)
http(s)://  WebBaseLoader — scrapes the page text
directory   Recursively loads all supported file types in the folder

All loaders return a flat list of models.Document objects (provider-native, no LangChain).

Usage
-----
from llm_toolbox.data_loader import load_documents
from llm_toolbox.models import Document

docs = load_documents("data/manuals/")          # whole folder
docs = load_documents("report.pdf")
docs = load_documents("prices.csv")
docs = load_documents("https://example.com/faq")
docs = load_documents("notes.json", json_schema=".[] | .text")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

try:
    from .models import Document
except ImportError:
    from models import Document

logger = logging.getLogger("llm_toolbox.data_loader")

# Maps file suffixes → loader factory
_SUFFIX_LOADERS = {
    ".pdf":  "_load_pdf",
    ".csv":  "_load_csv",
    ".txt":  "_load_text",
    ".md":   "_load_text",
    ".docx": "_load_docx",
    ".json": "_load_json",
}


def load_documents(
    source: str,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 80,
    json_schema: str = ".",
    recursive: bool = True,
) -> List[Document]:
    """Load *source* (file, folder, or URL) and return split ``Document`` objects.

    Args:
        source:        File path, directory path, or HTTP/HTTPS URL.
        chunk_size:    Max characters per chunk after splitting.
        chunk_overlap: Overlap between consecutive chunks.
        json_schema:   jq-style selector for JSON files (default: root value).
        recursive:     When *source* is a directory, recurse into sub-folders.

    Returns:
        List of ``Document`` objects ready to embed.
    """
    raw = _load_raw(source, json_schema=json_schema, recursive=recursive)
    if not raw:
        logger.warning("No documents loaded from '%s'", source)
        return []

    logger.info("Loaded %d raw document(s) from '%s'", len(raw), source)
    chunks = _split(raw, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("Split into %d chunk(s)", len(chunks))
    return chunks


# ── raw loading ───────────────────────────────────────────────────────────────

def _load_raw(source: str, *, json_schema: str, recursive: bool) -> List[Document]:
    """Dispatch to the appropriate loader without splitting."""
    s = source.strip()

    # URL
    if s.startswith("http://") or s.startswith("https://"):
        return _load_url(s)

    path = Path(s)

    # Directory — recurse over supported file types
    if path.is_dir():
        docs: List[Document] = []
        pattern = "**/*" if recursive else "*"
        for child in sorted(path.glob(pattern)):
            if child.is_file() and child.suffix.lower() in _SUFFIX_LOADERS:
                docs.extend(_load_raw(str(child), json_schema=json_schema, recursive=False))
        return docs

    if not path.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    method_name = _SUFFIX_LOADERS.get(path.suffix.lower())
    if method_name is None:
        raise ValueError(
            f"Unsupported file type '{path.suffix}'. "
            f"Supported: {', '.join(_SUFFIX_LOADERS)}, or an http(s):// URL."
        )

    return globals()[method_name](str(path), json_schema=json_schema)


def _load_pdf(path: str, **_) -> List[Document]:
    from langchain_community.document_loaders import PyPDFLoader
    lc_docs = PyPDFLoader(path).load()
    return [Document(content=doc.page_content, metadata=doc.metadata) for doc in lc_docs]


def _load_csv(path: str, **_) -> List[Document]:
    from langchain_community.document_loaders.csv_loader import CSVLoader
    lc_docs = CSVLoader(path).load()
    return [Document(content=doc.page_content, metadata=doc.metadata) for doc in lc_docs]


def _load_text(path: str, **_) -> List[Document]:
    from langchain_community.document_loaders import TextLoader
    lc_docs = TextLoader(path, encoding="utf-8").load()
    return [Document(content=doc.page_content, metadata=doc.metadata) for doc in lc_docs]


def _load_docx(path: str, **_) -> List[Document]:
    try:
        from langchain_community.document_loaders import Docx2txtLoader
        lc_docs = Docx2txtLoader(path).load()
        return [Document(content=doc.page_content, metadata=doc.metadata) for doc in lc_docs]
    except ImportError as exc:
        raise ImportError("Install docx2txt: pip install docx2txt") from exc


def _load_json(path: str, *, json_schema: str = ".", **_) -> List[Document]:
    from langchain_community.document_loaders import JSONLoader
    lc_docs = JSONLoader(file_path=path, jq_schema=json_schema, text_content=False).load()
    return [Document(content=doc.page_content, metadata=doc.metadata) for doc in lc_docs]


def _load_url(url: str, **_) -> List[Document]:
    from langchain_community.document_loaders import WebBaseLoader
    lc_docs = WebBaseLoader(url).load()
    return [Document(content=doc.page_content, metadata=doc.metadata) for doc in lc_docs]


# ── splitting ─────────────────────────────────────────────────────────────────

def _split(docs: List[Document], *, chunk_size: int, chunk_overlap: int) -> List[Document]:
    """Split documents into chunks using a simple text splitter (no LangChain)."""
    chunks = []
    chunk_id = 0
    
    for doc in docs:
        text = doc.content
        source = doc.metadata.get("source", "unknown") if doc.metadata else "unknown"
        
        # Simple sliding window split
        for i in range(0, len(text), chunk_size - chunk_overlap):
            if i + chunk_size > len(text):
                # Don't create tiny last chunks
                if len(text) - i < chunk_size // 4:
                    break
            chunk_text = text[i : i + chunk_size]
            metadata = {**(doc.metadata or {}), "start_index": i}
            chunk = Document(
                id=f"{source}:{chunk_id}",
                content=chunk_text,
                metadata=metadata,
            )
            chunks.append(chunk)
            chunk_id += 1
    
    return chunks
