# LangGraph Toolbox

Stateful LangGraph workflows that can run independently or next to `langchain_adapters`, `llm_toolbox`, and `my_toolbox`.

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

## Self-RAG example

```python
from langgraph_tolobox import SelfRAGAgent

agent = SelfRAGAgent(provider="ollama", llm_model_name="llama3.2:latest")
agent.add_documents([
    "LangGraph supports stateful orchestration.",
    "Self-RAG adds a reflection step after generation.",
])

result = agent.invoke("What is Self-RAG?")
print(result["generation"])
```

## Notes

- The repository directory name remains `langgraph_tolobox` for compatibility.
- The package is designed to share provider settings with the LangChain adapters toolbox.
- When `llm_toolbox` is present, you can reuse its prompt catalogs while keeping graph orchestration here.
