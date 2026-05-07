# LLM_Toolbox

Reusable LLM client layer, chat runtime, and RAG utilities used by My Toolbox.

## What's in this package

- `clients/`: provider-neutral client API (`get_llm_client`, `ChatMessage`) for Ollama, Gemini, Groq, Deepseek, and Kimi.
- `chat.py`: single chat entrypoint for CLI and web serving.
- `chat_history.py`: conversation persistence layer (SQLite by default, PostgreSQL optional).
- `query_data.py`: RAG response path over embedded documents.
- `vector_databases.py`: ChromaDB / Qdrant vector store integrations.
- `prompts/`: prompt catalogs and system prompt variants.

Structure note: keep `clients` in the package root at `llm_toolbox/llm_toolbox/clients` so imports stay simple: `from llm_toolbox.clients import ...`.

## Install

```bash
# from repository root
pip install -e .

# optional llm_toolbox extras
pip install -e "./llm_toolbox[dev]"
```

## Quick start

```bash
# CLI chat (single entrypoint)
python -m llm_toolbox.chat --interface cli --provider ollama --mode simple

# Web/API mode
python -m llm_toolbox.chat --interface web --host 0.0.0.0 --port 8000
```

## Client usage example

```python
from llm_toolbox.clients import ChatMessage, get_llm_client

client = get_llm_client(provider="ollama", model="llama3.2:latest")
reply = client.complete([
	ChatMessage(role="user", content="Give me a 3-line summary of this project.")
])
print(reply)
```

## Use Gemini instead of Ollama

Set `GOOGLE_API_KEY` and switch provider:

```python
from llm_toolbox.clients import get_llm_client

client = get_llm_client(provider="gemini", model="gemini-1.5-flash")
reply = client.complete(client.system_user_messages(None, "Hello!"))
```

## Notes

- Chat history DB defaults to SQLite at `llm_toolbox/chat_history.db`.
- To use PostgreSQL for chat history, set `CHAT_DB_BACKEND=postgres` and `CHAT_DB_DSN`.
- Package docs are in `llm_toolbox/docs/`.
