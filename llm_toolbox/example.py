"""llm_toolbox interactive examples.

Edit the config block below, set RUN_MODE, then run:
    python example.py

Modes: chat | rag | rag_history | all | none
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Config — edit here
# ---------------------------------------------------------------------------

# Direct chat target (single source of truth)
CHAT_MODEL = "cohere/Cohere-command-r-08-2024"
CHAT_ENDPOINT = "https://models.github.ai/inference"
CHAT_API_KEY = os.getenv("GITHUB_TOKEN", "")
# Optional override. Leave empty to infer from endpoint/model.
CHAT_PROVIDER = ""

EMBED_PROVIDER = "huggingface"   # local embeddings, no API key needed
EMBED_MODEL    = ""
EMBED_API_KEY = ""
EMBED_BASE_URL = ""

RUN_MODE = "chat"                # chat | rag | rag_history | all | none

# Single toggle for chat persistence.
# False -> in-memory interactive chat
# True  -> interactive chat with SQLite persistence
CHAT_PERSIST_HISTORY = True

DEBUG_STREAM = False             # True → print "|" between streamed chunks

CHAT_SYSTEM_PROMPT = (
    f"You are a helpful assistant for the llm_toolbox project. Be concise and friendly. "
    f"You are running as model '{CHAT_MODEL}'. "
    f"When asked about your model name or architecture, state this accurately."
)

# Documents used by rag / rag_history modes
RAG_DOCUMENTS = [
    {"content": "Ollama is best for fast local experimentation without external API tokens.",
     "metadata": {"source": "local_notes.md"}},
    {"content": "Gemini is useful for managed cloud inference and hosted embeddings.",
     "metadata": {"source": "provider_guide.md"}},
    {"content": "Start with Chroma for local RAG development — simple to run, persists on disk.",
     "metadata": {"source": "rag_setup.md"}},
    {"content": "Chat history can be stored in SQLite by default.",
     "metadata": {"source": "chat_history.md"}},
]
RAG_QUESTION         = "Which provider is best for quick local testing?"
RAG_HISTORY_QUESTION = "Based on what I said earlier, which retrieval setup should I start with?"

# Paths (kept inside llm_toolbox/db)
PACKAGE_ROOT = Path(__file__).resolve().parent
DB_ROOT = PACKAGE_ROOT / "db"
CHAT_DB_PATH = DB_ROOT / "chat_database.db"
CHROMA_PATH = DB_ROOT / "chroma"


def _setup_env() -> None:
    DB_ROOT.mkdir(parents=True, exist_ok=True)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CHAT_DB_PATH", str(CHAT_DB_PATH))
    os.environ.setdefault("CHROMA_PATH",  str(CHROMA_PATH))


def _make_client():
    from llm_toolbox.chat import build_chat_client

    return build_chat_client(
        model=CHAT_MODEL,
        endpoint=CHAT_ENDPOINT,
        api_key=CHAT_API_KEY,
        provider=CHAT_PROVIDER.strip().lower() or None,
    )


def _make_embedder():
    from llm_toolbox.embeddings import get_embedder

    kwargs = {}
    if EMBED_MODEL:
        kwargs["model"] = EMBED_MODEL
    if EMBED_API_KEY:
        kwargs["api_key"] = EMBED_API_KEY
    if EMBED_BASE_URL:
        kwargs["base_url"] = EMBED_BASE_URL
    return get_embedder(provider=EMBED_PROVIDER, **kwargs)


def _build_rag_db(collection_name: str):
    from llm_toolbox.models import ChromaDBConfig, Document
    from llm_toolbox.database_clients import ChromaDB
    embedder = _make_embedder()
    config = ChromaDBConfig(collection_name=collection_name, persist_directory=str(CHROMA_PATH))
    db = ChromaDB(config, embedder)
    docs = [Document(content=d["content"], metadata=d["metadata"]) for d in RAG_DOCUMENTS]
    db.add_documents(docs)
    return db


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def run_chat() -> None:
    from llm_toolbox.chat import Chat
    from llm_toolbox.clients import resolve_chat_provider

    client = _make_client()
    chat = Chat(
        client,
        system_prompt=CHAT_SYSTEM_PROMPT,
        debug_stream=DEBUG_STREAM,
    )

    if not CHAT_PERSIST_HISTORY:
        chat.run(persist=False)
        return

    from llm_toolbox.database_clients import get_chat_store

    store = get_chat_store(backend="sqlite", sqlite_path=str(CHAT_DB_PATH))
    provider = resolve_chat_provider(model=CHAT_MODEL, endpoint=CHAT_ENDPOINT, provider=CHAT_PROVIDER)
    conv = store.create_conversation(
        title=f"session-{uuid.uuid4().hex[:8]}",
        mode="simple",
        provider=provider,
        model=CHAT_MODEL,
        metadata={"persisted": True},
    )
    chat.run(persist=True, store=store, conversation_id=conv.id)


def run_rag() -> None:
    from llm_toolbox.clients import ChatMessage
    print(f"\nQuestion: {RAG_QUESTION}\n")
    db = _build_rag_db(f"rag-{uuid.uuid4().hex[:8]}")
    results = db.search(RAG_QUESTION, limit=3)
    context = "\n\n".join(r.document.content for r in results)
    sources  = [r.document.metadata.get("source", "?") for r in results]
    prompt = (
        "Answer only from the context below. If missing, say you do not know.\n\n"
        f"Context:\n{context}\n\nQuestion: {RAG_QUESTION}"
    )
    answer = _make_client().complete([ChatMessage(role="user", content=prompt)])
    print(answer)
    print(f"\nSources: {sources}")


def run_rag_history() -> None:
    from llm_toolbox.clients import resolve_chat_provider
    from llm_toolbox.database_clients import get_chat_store
    from llm_toolbox.clients import ChatMessage

    db = _build_rag_db(f"rag-history-{uuid.uuid4().hex[:8]}")
    store = get_chat_store(backend="sqlite", sqlite_path=str(CHAT_DB_PATH))
    provider = resolve_chat_provider(model=CHAT_MODEL, endpoint=CHAT_ENDPOINT, provider=CHAT_PROVIDER)
    conv = store.create_conversation(
        title="rag-history", mode="rag", provider=provider, model=CHAT_MODEL, metadata={}
    )
    store.add_message(conversation_id=conv.id, role="user",
                      content="I need a local-first setup with simple infrastructure.")
    store.add_message(conversation_id=conv.id, role="assistant",
                      content="Understood — I'll bias toward local models and simple storage.")

    results = db.search(RAG_HISTORY_QUESTION, limit=3)
    context = "\n\n".join(r.document.content for r in results)
    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in store.get_messages(conv.id)
    )
    prompt = (
        "Use both history and context. Match user's earlier preference.\n\n"
        f"History:\n{history}\n\nContext:\n{context}\n\nQuestion: {RAG_HISTORY_QUESTION}"
    )
    answer = _make_client().complete([ChatMessage(role="user", content=prompt)])
    print(f"\nQuestion: {RAG_HISTORY_QUESTION}\n")
    print(answer)
    store.add_message(conversation_id=conv.id, role="user", content=RAG_HISTORY_QUESTION)
    store.add_message(conversation_id=conv.id, role="assistant", content=answer)
    print(f"\nConversation id : {conv.id}")
    print(f"SQLite file     : {CHAT_DB_PATH}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_RUNNERS = {
    "chat":         run_chat,
    "rag":          run_rag,
    "rag_history":  run_rag_history,
}


def main() -> None:
    _setup_env()
    mode = RUN_MODE.strip().lower()
    if mode == "none":
        print("RUN_MODE=none — nothing to run. Edit the config block.")
        return
    if mode == "all":
        for fn in _RUNNERS.values():
            fn()
        return
    fn = _RUNNERS.get(mode)
    if fn:
        fn()
    else:
        print(f"Unknown RUN_MODE={RUN_MODE!r}. Choose: {', '.join(_RUNNERS)} | all | none")


if __name__ == "__main__":
    main()
