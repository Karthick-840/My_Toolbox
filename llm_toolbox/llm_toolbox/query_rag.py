"""Query a populated vector database with a natural language question.

CORE PROVIDER-NATIVE IMPLEMENTATION (no LangChain for retrieval)

Pluggable embedding provider and vector DB backend — must match what was used
during populate_rag.py.

CLI examples
------------
# Default: Ollama embeddings, Chroma DB
python query_rag.py "What is the return policy?"

# Gemini embeddings
python query_rag.py "Explain quantum entanglement" --embed gemini

# Qdrant backend
python query_rag.py "What are the rules?" --db qdrant

# Use Gemini as the LLM for answering (still Ollama for embeddings)
python query_rag.py "Summarise chapter 1" --llm gemini
"""

import argparse
import os

try:
    from .embeddings import get_embedder
    from .database_clients import ChromaDB, QdrantDB, ChromaDBConfig, QdrantDBConfig
    from .clients import ChatMessage, get_llm_client
except ImportError:
    from embeddings import get_embedder
    from database_clients import ChromaDB, QdrantDB, ChromaDBConfig, QdrantDBConfig
    from clients import ChatMessage, get_llm_client

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")

PROMPT_TEMPLATE = """Answer the question based ONLY on the following context.
If the answer is not in the context, say "I don't know."

Context:
{context}

---
Question: {question}
"""


def query_rag(
    query_text: str,
    *,
    embed_provider: str | None = None,
    db_backend: str = "chroma",
    llm_provider: str = "ollama",
    collection: str = "documents",
    top_k: int = 5,
) -> str:
    """Run a RAG query and return the answer string."""
    embedder = get_embedder(embed_provider)

    # ── retrieve context ──────────────────────────────────────────────────────
    if db_backend == "chroma":
        config = ChromaDBConfig(
            collection_name=collection,
            persist_directory=CHROMA_PATH,
        )
        db = ChromaDB(config, embedder)
        results = db.search(query_text, limit=top_k)
    elif db_backend == "qdrant":
        config = QdrantDBConfig(
            collection_name=collection,
            location=os.getenv("QDRANT_URL", ":memory:"),
        )
        db = QdrantDB(config, embedder)
        results = db.search(query_text, limit=top_k)
    else:
        raise ValueError(f"Unknown db backend: {db_backend}")

    if not results:
        return "No relevant documents found in the database."

    context = "\n\n---\n\n".join(result.document.content for result in results)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query_text)
    sources = list({result.document.metadata.get("source", "unknown") for result in results if result.document.metadata})

    # ── generate answer using adapters ────────────────────────────────────────
    llm_client = get_llm_client(llm_provider)
    answer = llm_client.complete([ChatMessage(role="user", content=prompt)])

    return f"{answer}\n\nSources: {sources}"


def main():
    parser = argparse.ArgumentParser(description="Query a RAG vector database (provider-native).")
    parser.add_argument("query_text", type=str, help="The question to ask.")
    parser.add_argument("--embed",      default=None,     help="Embedding provider: ollama|gemini|huggingface|bedrock")
    parser.add_argument("--db",         default="chroma", choices=["chroma", "qdrant"])
    parser.add_argument("--llm",        default="ollama", choices=["ollama", "gemini", "groq"])
    parser.add_argument("--collection", default="documents")
    parser.add_argument("--top-k",      type=int, default=5)
    args = parser.parse_args()

    answer = query_rag(
        args.query_text,
        embed_provider=args.embed,
        db_backend=args.db,
        llm_provider=args.llm,
        collection=args.collection,
        top_k=args.top_k,
    )
    print(answer)


if __name__ == "__main__":
    main()
