"""Standalone LangChain interoperability toolbox.

This package can run independently or alongside llm_toolbox and my_toolbox.
It provides provider-aware LangChain/LangGraph helpers for Gemini, OpenAI,
DeepSeek, and Ollama.
"""

from .provider_factory import (
    ProviderDefaults,
    get_chat_model,
    get_embedding_model,
    get_provider_defaults,
    supported_providers,
)

__all__ = [
    "ProviderDefaults",
    "get_chat_model",
    "get_embedding_model",
    "get_provider_defaults",
    "supported_providers",
    "LangChainToolbox",
]


def __getattr__(name: str):
    if name == "LangChainToolbox":
        from .toolbox import LangChainToolbox

        return LangChainToolbox
    raise AttributeError(name)
