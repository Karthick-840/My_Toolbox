"""Populate a vector database from any supported data source.

PROVIDER-AGNOSTIC — no LangChain dependency.

Supported embed providers : ollama (default), gemini, huggingface, bedrock
Supported vector databases : chroma (default), qdrant
Supported sources          : directory, PDF, CSV, TXT, MD, DOCX, JSON, URL

CLI examples
------------
# Ingest a folder using Ollama embeddings → Chroma (defaults)
python populate_rag.py --source data/

# Ingest a PDF with Gemini embeddings
python populate_rag.py --source report.pdf --embed gemini

# Ingest a URL into Qdrant
python populate_rag.py --source https://example.com/faq --db qdrant

# Reset the DB and re-ingest
python populate_rag.py --source data/ --reset
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import shutil
from io import StringIO
from pathlib import Path
from typing import List

try:
    from .embeddings import get_embedder
    from .database_clients import ChromaDB, QdrantDB, ChromaDBConfig, Document, QdrantDBConfig
except ImportError:
    from embeddings import get_embedder
    from database_clients import ChromaDB, QdrantDB, ChromaDBConfig, Document, QdrantDBConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("populate_rag")

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")
DATA_PATH   = os.getenv("DATA_PATH",   "data")

_SUPPORTED_SUFFIXES = {".pdf", ".csv", ".txt", ".md", ".docx", ".json"}


# ── Document loading (provider-agnostic) ──────────────────────────────────────

def load_documents(
    source: str,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 80,
    json_field: str | None = None,
    recursive: bool = True,
) -> List[Document]:
    """Load *source* (file path, directory, or URL) and return split Document chunks.

    Args:
        source:       File path, directory, or HTTP/HTTPS URL.
        chunk_size:   Max characters per chunk.
        chunk_overlap: Overlap characters between consecutive chunks.
        json_field:   Key name to extract from each JSON object (default: full stringify).
        recursive:    When source is a directory, recurse into sub-folders.
    """
    raw = _load_raw(source, json_field=json_field, recursive=recursive)
    if not raw:
        logger.warning("No documents loaded from '%s'", source)
        return []
    logger.info("Loaded %d raw document(s) from '%s'", len(raw), source)
    chunks = _split(raw, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("Split into %d chunk(s)", len(chunks))
    return chunks


def _load_raw(source: str, *, json_field: str | None, recursive: bool) -> List[Document]:
    s = source.strip()

    if s.startswith("http://") or s.startswith("https://"):
        return _load_url(s)

    path = Path(s)

    if path.is_dir():
        docs: List[Document] = []
        pattern = "**/*" if recursive else "*"
        for child in sorted(path.glob(pattern)):
            if child.is_file() and child.suffix.lower() in _SUPPORTED_SUFFIXES:
                docs.extend(_load_raw(str(child), json_field=json_field, recursive=False))
        return docs

    if not path.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(str(path))
    if suffix == ".csv":
        return _load_csv(str(path))
    if suffix in (".txt", ".md"):
        return _load_text(str(path))
    if suffix == ".docx":
        return _load_docx(str(path))
    if suffix == ".json":
        return _load_json(str(path), json_field=json_field)
    raise ValueError(f"Unsupported file type '{suffix}'. Supported: {_SUPPORTED_SUFFIXES}, or an http(s):// URL.")


def _load_pdf(path: str) -> List[Document]:
    try:
        import pypdf
    except ImportError as exc:
        raise ImportError("Install pypdf: pip install pypdf") from exc
    docs = []
    with open(path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                docs.append(Document(content=text, metadata={"source": path, "page": page_num}))
    return docs


def _load_csv(path: str) -> List[Document]:
    docs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            text = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
            docs.append(Document(content=text, metadata={"source": path, "row": i}))
    return docs


def _load_text(path: str) -> List[Document]:
    text = Path(path).read_text(encoding="utf-8")
    return [Document(content=text, metadata={"source": path})]


def _load_docx(path: str) -> List[Document]:
    try:
        import docx
    except ImportError as exc:
        raise ImportError("Install python-docx: pip install python-docx") from exc
    doc = docx.Document(path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [Document(content=text, metadata={"source": path})]


def _load_json(path: str, *, json_field: str | None = None) -> List[Document]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else [data]
    docs = []
    for i, item in enumerate(items):
        if json_field and isinstance(item, dict):
            text = str(item.get(json_field, item))
        else:
            text = json.dumps(item, ensure_ascii=False)
        docs.append(Document(content=text, metadata={"source": path, "index": i}))
    return docs


def _load_url(url: str) -> List[Document]:
    import urllib.request
    from html.parser import HTMLParser

    class _TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._buf: list[str] = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "head"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style", "head"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip and data.strip():
                self._buf.append(data.strip())

        def get_text(self):
            return "\n".join(self._buf)

    with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310 — URL provided by trusted caller
        html = resp.read().decode(resp.headers.get_content_charset("utf-8"), errors="replace")

    parser = _TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    return [Document(content=text, metadata={"source": url})]


def _split(docs: List[Document], *, chunk_size: int, chunk_overlap: int) -> List[Document]:
    """Sliding-window character splitter (no external deps)."""
    chunks = []
    chunk_id = 0
    for doc in docs:
        text = doc.content
        source = (doc.metadata or {}).get("source", "unknown")
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            # Skip tiny trailing fragments
            if len(chunk_text) < chunk_size // 4 and chunks:
                break
            chunks.append(Document(
                id=f"{source}:{chunk_id}",
                content=chunk_text,
                metadata={**(doc.metadata or {}), "start_index": start},
            ))
            chunk_id += 1
            start += chunk_size - chunk_overlap
    return chunks


# ── Chunk ID stamping ─────────────────────────────────────────────────────────

def calculate_chunk_ids(chunks: List[Document]) -> List[Document]:
    """Stamp stable IDs like 'data/file.pdf:page:chunk_idx' on each chunk."""
    last_source_page = None
    current_chunk_index = 0

    for chunk in chunks:
        source = (chunk.metadata or {}).get("source", "unknown")
        page   = (chunk.metadata or {}).get("page", 0)
        current_source_page = f"{source}:{page}"

        if current_source_page == last_source_page:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
        last_source_page = current_source_page

        chunk_id = f"{current_source_page}:{current_chunk_index}"
        if chunk.metadata is None:
            chunk.metadata = {}
        chunk.metadata["id"] = chunk_id
        chunk.id = chunk_id

    return chunks


# ── DB management ─────────────────────────────────────────────────────────────

def clear_database(db_type: str):
    if db_type == "chroma":
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
            logger.info("Cleared Chroma database at %s", CHROMA_PATH)
    # Qdrant in-memory is cleared automatically on restart


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Populate a vector DB from any data source.")
    parser.add_argument("--source",        default=DATA_PATH,    help="File, folder, or URL to ingest")
    parser.add_argument("--embed",         default=None,         help="Embedding provider: ollama|gemini|huggingface|bedrock")
    parser.add_argument("--db",            default="chroma",     choices=["chroma", "qdrant"])
    parser.add_argument("--collection",    default="documents",  help="Collection name (default: documents)")
    parser.add_argument("--chunk-size",    type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=80)
    parser.add_argument("--json-field",    default=None,         help="JSON key to extract text from")
    parser.add_argument("--reset",         action="store_true",  help="Wipe the DB before ingesting")
    args = parser.parse_args()

    if args.reset:
        logger.info("Clearing database...")
        clear_database(args.db)

    chunks = load_documents(
        args.source,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        json_field=args.json_field,
    )
    if not chunks:
        logger.error("No documents loaded. Aborting.")
        return

    chunks = calculate_chunk_ids(chunks)

    embedder = get_embedder(args.embed)
    logger.info("Using embedder: %s", embedder.__class__.__name__)

    if args.db == "chroma":
        config = ChromaDBConfig(collection_name=args.collection, persist_directory=CHROMA_PATH)
        db = ChromaDB(config, embedder)
        db.add_documents(chunks)
        logger.info("Upserted %d chunk(s) to Chroma '%s'", len(chunks), args.collection)
    elif args.db == "qdrant":
        config = QdrantDBConfig(
            collection_name=args.collection,
            location=os.getenv("QDRANT_URL", ":memory:"),
        )
        db = QdrantDB(config, embedder)
        db.add_documents(chunks)
        logger.info("Upserted %d chunk(s) to Qdrant '%s'", len(chunks), args.collection)


if __name__ == "__main__":
    main()
