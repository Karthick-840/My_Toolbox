"""Provider-aware LangChain factories for chat models and embeddings.

This module keeps LangChain/LangGraph integrations independent from llm_toolbox
while remaining compatible with its provider choices and environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class ProviderDefaults:
    chat_model: str
    embedding_model: str


_DEFAULTS: Dict[str, ProviderDefaults] = {
    "ollama": ProviderDefaults(
        chat_model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:latest"),
        embedding_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    ),
    "gemini": ProviderDefaults(
        chat_model=os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash"),
        embedding_model=os.getenv("GEMINI_EMBED_MODEL", "models/embedding-001"),
    ),
    "openai": ProviderDefaults(
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        embedding_model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large"),
    ),
    "deepseek": ProviderDefaults(
        chat_model=os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat"),
        embedding_model=os.getenv("DEEPSEEK_EMBED_MODEL", "text-embedding-3-large"),
    ),
}


def supported_providers() -> Tuple[str, ...]:
    return tuple(_DEFAULTS.keys())


def get_provider_defaults(provider: str) -> ProviderDefaults:
    key = provider.strip().lower()
    if key not in _DEFAULTS:
        raise ValueError(f"Unsupported provider '{provider}'. Choose from: {', '.join(_DEFAULTS)}")
    return _DEFAULTS[key]


def get_chat_model(provider: str, model: str | None = None, temperature: float = 0.2, **kwargs: Any):
    """Return a LangChain chat model for the requested provider."""

    key = provider.strip().lower()
    defaults = get_provider_defaults(key)
    resolved_model = model or defaults.chat_model

    if key == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=resolved_model,
            temperature=temperature,
            base_url=kwargs.get("base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")),
        )

    if key == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is required for gemini provider")
        return ChatGoogleGenerativeAI(model=resolved_model, temperature=temperature, google_api_key=api_key)

    if key == "openai":
        from langchain_openai import ChatOpenAI

        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for openai provider")
        return ChatOpenAI(
            model=resolved_model,
            temperature=temperature,
            api_key=api_key,
            base_url=kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL"),
        )

    if key == "deepseek":
        from langchain_openai import ChatOpenAI

        api_key = kwargs.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for deepseek provider")
        return ChatOpenAI(
            model=resolved_model,
            temperature=temperature,
            api_key=api_key,
            base_url=kwargs.get("base_url") or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )

    raise ValueError(f"Unsupported provider '{provider}'. Choose from: {', '.join(_DEFAULTS)}")


def get_embedding_model(provider: str, model: str | None = None, **kwargs: Any):
    """Return a LangChain embeddings implementation for the requested provider."""

    key = provider.strip().lower()
    defaults = get_provider_defaults(key)
    resolved_model = model or defaults.embedding_model

    if key == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            from langchain_community.embeddings.ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=resolved_model,
            base_url=kwargs.get("base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")),
        )

    if key == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is required for gemini provider")
        return GoogleGenerativeAIEmbeddings(model=resolved_model, google_api_key=api_key)

    if key == "openai":
        from langchain_openai import OpenAIEmbeddings

        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for openai provider")
        return OpenAIEmbeddings(
            model=resolved_model,
            api_key=api_key,
            base_url=kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL"),
        )

    if key == "deepseek":
        from langchain_openai import OpenAIEmbeddings

        api_key = kwargs.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for deepseek provider")
        return OpenAIEmbeddings(
            model=resolved_model,
            api_key=api_key,
            base_url=kwargs.get("base_url") or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )

    raise ValueError(f"Unsupported provider '{provider}'. Choose from: {', '.join(_DEFAULTS)}")