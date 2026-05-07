"""Runtime selection for agentic flows across local Ollama and Gemini API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from llm_toolbox.adapters import ChatMessage, get_llm_client

Provider = Literal["ollama", "gemini"]


@dataclass
class RuntimeConfig:
    provider: Provider = "ollama"
    model: str = "gemma3:latest"
    ollama_base_url: str = "http://localhost:11434"
    gemini_api_key: Optional[str] = None


class AgenticRuntime:
    """Simple runtime router reused by Pydantic-AI or LangGraph layers."""

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        kwargs = {}
        if config.provider == "ollama":
            kwargs["base_url"] = config.ollama_base_url
        elif config.provider == "gemini" and config.gemini_api_key:
            kwargs["api_key"] = config.gemini_api_key

        self.client = get_llm_client(provider=config.provider, model=config.model, **kwargs)

    def ask(self, user_prompt: str, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        messages = self.client.system_user_messages(system_prompt=system_prompt, user_prompt=user_prompt)
        return self.client.complete(messages=messages, temperature=temperature)


def default_coding_runtime() -> AgenticRuntime:
    """Local-first default runtime for coding assistant workflows."""

    return AgenticRuntime(RuntimeConfig(provider="ollama", model="gemma3:latest"))
