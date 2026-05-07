# LangChain Adapters Toolbox

Provider-aware LangChain helpers that work in two modes:

1. Standalone LangChain mode
2. Preferred llm_toolbox bridge mode, with standalone fallback

my_toolbox is optional and only used for logging or operational wrappers.

## Supported providers

- Ollama
- Gemini
- OpenAI
- DeepSeek

## Install

Base install:

```bash
pip install -e .
```

Provider extras:

```bash
pip install -e .[ollama]
pip install -e .[gemini]
pip install -e .[openai]
pip install -e .[deepseek]
```

If you want the sibling toolbox integrations:

```bash
pip install -e .[integrations]
```

## Quick start

High-level RAG helper:

```python
from langchain_adapters import LangChainToolbox

toolbox = LangChainToolbox(provider="ollama")
toolbox.ingest_texts([
    "RAG combines retrieval with generation.",
    "DeepSeek and OpenAI can be used through OpenAI-compatible interfaces.",
])
print(toolbox.ask("What is RAG?"))
```

Unified chat interface with preferred llm_toolbox backend:

```python
from langchain_adapters import UnifiedToolboxLLM

llm = UnifiedToolboxLLM(provider="gemini", backend="auto")
print(llm.invoke("List 5 ideas for improving latency in RAG systems."))
```

## CLI

```bash
python -m langchain_adapters.cli --provider deepseek --prompt "Explain vector DB indexing"
python -m langchain_adapters.cli --provider ollama --backend auto --prompt "Hello"
```

## Environment variables

- OPENAI_API_KEY
- GOOGLE_API_KEY or GEMINI_API_KEY
- DEEPSEEK_API_KEY
- OLLAMA_BASE_URL

Common model overrides:

- OPENAI_CHAT_MODEL
- GEMINI_CHAT_MODEL
- DEEPSEEK_CHAT_MODEL
- OLLAMA_CHAT_MODEL

## Notes

- backend="auto" prefers llm_toolbox when it is importable.
- OpenAI still uses LangChain directly in auto mode because llm_toolbox does not implement that provider yet.
- my_toolbox is optional and only used when logging integration is enabled.
# LangChain Adapters Toolbox

Standalone LangChain helpers that can also sit next to `llm_toolbox` and `my_toolbox`.

## Supported providers

- Ollama
- Gemini
- OpenAI
- DeepSeek

## Install

```bash
pip install -e .
pip install -e .[ollama]
pip install -e .[gemini]
pip install -e .[openai]
pip install -e .[deepseek]
```

## Quick start

```python
from langchain_adapters import LangChainToolbox

toolbox = LangChainToolbox(provider="ollama")
toolbox.ingest_texts([
    "RAG combines retrieval with generation.",
    "DeepSeek and OpenAI can be used through OpenAI-compatible interfaces.",
])
answer = toolbox.ask("What is RAG?")
print(answer)
```

## Provider examples

```python
from langchain_adapters import LangChainToolbox

ollama_tb = LangChainToolbox(provider="ollama", chat_model="llama3.2:latest")
gemini_tb = LangChainToolbox(provider="gemini", chat_model="gemini-1.5-flash")
openai_tb = LangChainToolbox(provider="openai", chat_model="gpt-4o-mini")
deepseek_tb = LangChainToolbox(provider="deepseek", chat_model="deepseek-chat")
```

## Integration notes

- Use standalone when you only want LangChain/LangGraph workflows.
- Use alongside `llm_toolbox` when you want shared prompt catalogs or provider-native utilities.
- Use alongside `my_toolbox` when you want to layer your own operational tooling around agents.
# langchain_adapters

A provider-agnostic LangChain toolbox that can run:

1. Standalone (independent mode)
2. With llm_toolbox native clients (bridge mode)
3. With optional my_toolbox logging decorators

## Providers

- Ollama
- Gemini
- OpenAI
- DeepSeek

## Quick Start

```python
from langchain_adapters import UnifiedToolboxLLM

llm = UnifiedToolboxLLM(provider="openai", backend="langchain")
print(llm.invoke("Write a 3-line summary of retrieval-augmented generation."))
```

## Bridge Mode (auto)

```python
from langchain_adapters import UnifiedToolboxLLM

llm = UnifiedToolboxLLM(provider="gemini", backend="auto")
# Uses llm_toolbox client if available; otherwise uses LangChain provider.
print(llm.invoke("List 5 ideas for improving latency in RAG systems."))
```

## CLI

```bash
python -m langchain_adapters.cli --provider deepseek --prompt "Explain vector DB indexing"
python -m langchain_adapters.cli --provider ollama --backend auto --prompt "Hello"
```

## Environment Variables

- OPENAI_API_KEY
- GOOGLE_API_KEY
- DEEPSEEK_API_KEY
- OLLAMA_BASE_URL (optional, default: http://localhost:11434)

Model overrides:

- OPENAI_MODEL
- GEMINI_MODEL
- DEEPSEEK_MODEL
- OLLAMA_MODEL

## Optional Dependencies

Install only what you use:

```bash
pip install langchain-core langchain-openai langchain-google-genai langchain-ollama
```

For community fallback classes:

```bash
pip install langchain-community
```
