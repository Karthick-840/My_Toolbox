"""LangChain-compatible embedding factory (deprecated/optional).

DEPRECATED: Use llm_toolbox.embeddings.get_embedder() instead for provider-native embeddings.

This module provides LangChain Embeddings objects wrapping provider SDKs.
For new code, use the core provider-native layer:

    from llm_toolbox.embeddings import get_embedder
    embedder = get_embedder("ollama")          # Returns BaseEmbedder, no LangChain
    vecs = embedder.embed_documents(docs)     # Works with models.Document

LangChain variant (legacy):

    from llm_toolbox.langchain_adapters.embeddings import get_langchain_embeddings
    embed_fn = get_langchain_embeddings("ollama")  # Returns LangChain Embeddings
    vecs = embed_fn.embed_documents(docs)          # Works with LangChain Document

Supported providers
-------------------
ollama      OllamaEmbeddings  - local Ollama server (default model: nomic-embed-text)
gemini      Google Generative AI embeddings - requires GOOGLE_API_KEY
openai      OpenAIEmbeddings - requires OPENAI_API_KEY
deepseek    OpenAI-compatible embeddings endpoint - requires DEEPSEEK_API_KEY
huggingface HuggingFaceEmbeddings  - sentence-transformers, fully local
bedrock     BedrockEmbeddings - AWS Bedrock (requires AWS credentials)
"""

from __future__ import annotations

import os
from typing import Any


def get_langchain_embeddings(provider: str | None = None, model: str | None = None, **kwargs: Any):
    """Return a LangChain-compatible embedding object for *provider* (DEPRECATED).

    Use llm_toolbox.embeddings.get_embedder() for new code (provider-native, no LangChain).

    Provider resolution order:
      1. ``provider`` argument
      2. ``EMBEDDING_PROVIDER`` environment variable
      3. ``"ollama"`` (default)
    """
    resolved = (provider or os.getenv("EMBEDDING_PROVIDER", "ollama")).strip().lower()

    if resolved == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            from langchain_community.embeddings.ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            model=model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            base_url=kwargs.get("base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")),
        )

    if resolved == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=model or "models/embedding-001",
            google_api_key=kwargs.get("api_key") or os.environ["GOOGLE_API_KEY"],
        )

    if resolved == "openai":
        from langchain_openai import OpenAIEmbeddings
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for openai embeddings provider")
        return OpenAIEmbeddings(
            model=model or os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large"),
            api_key=api_key,
            base_url=kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL"),
        )

    if resolved == "deepseek":
        from langchain_openai import OpenAIEmbeddings
        api_key = kwargs.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for deepseek embeddings provider")
        return OpenAIEmbeddings(
            model=model or os.getenv("DEEPSEEK_EMBED_MODEL", "text-embedding-3-large"),
            api_key=api_key,
            base_url=kwargs.get("base_url") or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )

    if resolved == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=model or os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        )

    if resolved == "bedrock":
        from langchain_community.embeddings.bedrock import BedrockEmbeddings
        return BedrockEmbeddings(
            credentials_profile_name=kwargs.get("profile", "default"),
            region_name=kwargs.get("region", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
            model_id=model or "amazon.titan-embed-text-v1",
        )

    raise ValueError(
        f"Unknown embedding provider '{resolved}'. "
        "Choose from: ollama, gemini, openai, deepseek, huggingface, bedrock"
    )


# Backward compat alias
def get_embedding_function(provider: str | None = None, model: str | None = None, **kwargs: Any):
    """Alias for get_langchain_embeddings (for backward compatibility)."""
    return get_langchain_embeddings(provider=provider, model=model, **kwargs)
