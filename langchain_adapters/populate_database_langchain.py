"""Populate a vector database using LangChain backends (OPTIONAL variant).

DEPRECATED: Use llm_toolbox.populate_database for core provider-native implementation.

This module provides LangChain-based population using langchain_chroma and langchain_community.
For new code, use the core provider-native layer in parent package:

    from llm_toolbox.populate_database import main as populate_core
    # Uses: BaseEmbedder + vector_databases.py (no LangChain)

LangChain variant (legacy interop):

    from llm_toolbox.langchain_adapters.populate_database import main as populate_langchain
    # Uses: langchain_chroma.Chroma + langchain_community (LangChain-based)
"""

import argparse
import logging
import os
import shutil

try:
    from .embeddings import get_embedding_function
except ImportError:
    from langchain_adapters.embeddings import get_embedding_function

try:
    from llm_toolbox.data_loader import load_documents
except ImportError:
    from llm_toolbox.llm_toolbox.data_loader import load_documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("populate_database_langchain")

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")
DATA_PATH   = os.getenv("DATA_PATH",   "data")


def main():
    parser = argparse.ArgumentParser(description="Populate a vector DB from any data source (LangChain variant - DEPRECATED).")
    parser.add_argument("--source",  default=DATA_PATH,   help="File, folder, or URL to ingest (default: DATA_PATH env / 'data')")
    parser.add_argument("--embed",   default=None,        help="Embedding provider: ollama|gemini|huggingface|bedrock (default: EMBEDDING_PROVIDER env / ollama)")
    parser.add_argument("--db",      default="chroma",    choices=["chroma", "qdrant"], help="Vector database backend (default: chroma)")
    parser.add_argument("--collection", default="documents", help="Collection name (default: documents)")
    parser.add_argument("--chunk-size",    type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=80)
    parser.add_argument("--reset",   action="store_true", help="Wipe the DB before ingesting")
    args = parser.parse_args()

    if args.reset:
        logger.info("Clearing database at %s", CHROMA_PATH)
        clear_database()

    # 1. Load + split all documents (returns models.Document, compatible with LCH)
    chunks = load_documents(
        args.source,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    if not chunks:
        logger.error("No documents loaded. Aborting.")
        return

    # 2. Convert models.Document to LangChain Document for LCH backends
    lc_chunks = []
    for chunk in chunks:
        from langchain.schema import Document as LCDocument
        lc_chunks.append(LCDocument(page_content=chunk.content, metadata=chunk.metadata or {}))

    # 3. Stamp stable IDs on every chunk
    lc_chunks = calculate_chunk_ids(lc_chunks)

    # 4. Get embedding function (LangChain variant)
    embed_fn = get_embedding_function(args.embed)

    # 5. Upsert into the chosen vector DB
    if args.db == "chroma":
        _add_to_chroma(lc_chunks, embed_fn, collection=args.collection)
    elif args.db == "qdrant":
        _add_to_qdrant(lc_chunks, embed_fn, collection=args.collection)


def _add_to_chroma(chunks, embed_fn, collection: str = "documents"):
    from langchain_chroma import Chroma
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embed_fn,
        collection_name=collection,
    )
    existing_ids = set(db.get(include=[])["ids"])
    logger.info("Existing docs in Chroma: %d", len(existing_ids))

    new_chunks = [c for c in chunks if c.metadata.get("id") not in existing_ids]
    if new_chunks:
        logger.info("Adding %d new chunk(s)", len(new_chunks))
        db.add_documents(new_chunks, ids=[c.metadata.get("id") for c in new_chunks])
    else:
        logger.info("No new documents to add")


def _add_to_qdrant(chunks, embed_fn, collection: str = "documents"):
    from langchain_community.vectorstores import Qdrant
    Qdrant.from_documents(
        chunks,
        embed_fn,
        location=os.getenv("QDRANT_URL", ":memory:"),
        collection_name=collection,
    )
    logger.info("Upserted %d chunk(s) to Qdrant collection '%s'", len(chunks), collection)


def calculate_chunk_ids(chunks):
    """Calculate stable IDs like 'data/monopoly.pdf:6:2' for LangChain Document objects."""
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", 0)
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()
