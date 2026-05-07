"""Query a vector database using LangChain backends (OPTIONAL variant).

DEPRECATED: Use llm_toolbox.query_data for core provider-native implementation.

This module provides LangChain-based querying using langchain_chroma and langchain LLM clients.
For new code, use the core provider-native layer in parent package:

    from llm_toolbox.query_data import query_rag
    # Uses: BaseEmbedder + vector_databases.py + adapters (no LangChain for retrieval)

LangChain variant (legacy interop):

    from llm_toolbox.langchain_adapters.query_data_langchain import query_rag
    # Uses: langchain_chroma.Chroma + langchain LLMs (full LangChain stack)
"""

import argparse
import os

try:
    from ..langchain_adapters.embeddings import get_embedding_function
except ImportError:
    from langchain_adapters.embeddings import get_embedding_function

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
    """Run a RAG query using LangChain backends (DEPRECATED - use parent package version)."""
    embed_fn = get_embedding_function(embed_provider)

    # ── retrieve context ──────────────────────────────────────────────────────
    if db_backend == "chroma":
        from langchain_chroma import Chroma
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embed_fn,
            collection_name=collection,
        )
    elif db_backend == "qdrant":
        from langchain_community.vectorstores import Qdrant
        from qdrant_client import QdrantClient
        client = QdrantClient(url=os.getenv("QDRANT_URL", ":memory:"))
        db = Qdrant(client=client, collection_name=collection, embeddings=embed_fn)
    else:
        raise ValueError(f"Unknown db backend: {db_backend}")

    results = db.similarity_search_with_score(query_text, k=top_k)
    if not results:
        return "No relevant documents found in the database."

    context = "\n\n---\n\n".join(doc.page_content for doc, _score in results)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query_text)
    sources = list({doc.metadata.get("source", "unknown") for doc, _ in results})

    # ── generate answer ───────────────────────────────────────────────────────
    if llm_provider == "ollama":
        try:
            from langchain_ollama import OllamaLLM as Ollama
        except ImportError:
            from langchain_community.llms.ollama import Ollama
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        answer = Ollama(model=model_name).invoke(prompt)
    elif llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        answer = ChatGoogleGenerativeAI(model=model_name).invoke(prompt).content
    elif llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        answer = ChatOpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY")).invoke(prompt).content
    elif llm_provider == "deepseek":
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        answer = ChatOpenAI(
            model=model_name,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        ).invoke(prompt).content
    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")

    return f"{answer}\n\nSources: {sources}"


def main():
    parser = argparse.ArgumentParser(description="Query a RAG vector database (LangChain variant - DEPRECATED).")
    parser.add_argument("query_text", type=str, help="The question to ask.")
    parser.add_argument("--embed",      default=None,     help="Embedding provider: ollama|gemini|huggingface|bedrock")
    parser.add_argument("--db",         default="chroma", choices=["chroma", "qdrant"])
    parser.add_argument("--llm",        default="ollama", choices=["ollama", "gemini", "openai", "deepseek"])
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
