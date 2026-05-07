"""
Provider-native embedders — no LangChain dependency.

Each class calls the provider SDK directly and shares the same interface:
  embed_documents(List[Document]) -> List[List[float]]
  embed_query(str)                -> List[float]

Supported providers (config-driven, reduces boilerplate):
- ollama         (local REST API)
- gemini         (Google Generative AI)
- openai         (OpenAI-compatible)
- deepseek       (OpenAI-compatible)
- kimi           (OpenAI-compatible)
- huggingface    (sentence-transformers, fully local)
- bedrock        (AWS Bedrock)

Factory
-------
from llm_toolbox.embeddings import get_embedder

embedder = get_embedder("ollama")
embedder = get_embedder("gemini", api_key="...")
embedder = get_embedder("openai", api_key="...")
embedder = get_embedder("huggingface", model="BAAI/bge-small-en-v1.5")
vecs = embedder.embed_documents(docs)
vec  = embedder.embed_query("What is RAG?")
"""

from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List

from pydantic import BaseModel, Field

try:
    from .database_clients import Document
except ImportError:
    from database_clients import Document

try:
    from .clients import get_provider_config
except ImportError:
    from clients import get_provider_config


# ── Embedding-specific types ──────────────────────────────────────────────────

class TaskType(str, Enum):
    """Task types supported by Gemini embeddings."""

    RETRIEVAL_QUERY = "RETRIEVAL_QUERY"
    RETRIEVAL_DOCUMENT = "RETRIEVAL_DOCUMENT"
    SEMANTIC_SIMILARITY = "SEMANTIC_SIMILARITY"
    CLASSIFICATION = "CLASSIFICATION"
    CLUSTERING = "CLUSTERING"


class EmbeddingConfig(BaseModel):
    """Configuration for Gemini embeddings."""

    model_name: str = Field(
        "models/embedding-001", description="Name of the embedding model to use."
    )
    api_key: str = Field(..., description="API key for the Gemini API.")
    vector_size: int = Field(768, description="Expected dimension of the embedding vectors.")


# ── Base interface ────────────────────────────────────────────────────────────

class BaseEmbedder(ABC):
    """Common interface for all provider embedders."""

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """Embed a list of Document objects → list of float vectors."""

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string → float vector."""

    @classmethod
    def from_config(cls, config: EmbeddingConfig) -> "BaseEmbedder":
        raise NotImplementedError(f"{cls.__name__} does not support from_config()")


# ── Gemini ────────────────────────────────────────────────────────────────────

class GeminiEmbedder(BaseEmbedder):
    """Embeds via Google Gemini API (google-generativeai SDK)."""

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        cfg = get_provider_config("gemini", category="embedder")
        model = model or cfg.default_model
        if not model:
            raise ValueError("Missing default model for gemini in clients config")
        super().__init__(model)
        import google.generativeai as genai
        genai.configure(api_key=api_key or os.environ[cfg.api_key_env or "GOOGLE_API_KEY"])
        self._genai = genai

    @classmethod
    def from_config(cls, config: EmbeddingConfig) -> "GeminiEmbedder":
        return cls(model=config.model_name, api_key=config.api_key)

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        contents = [doc.content for doc in documents]
        response = self._genai.embed_content(
            model=self.model,
            content=contents,
            task_type=TaskType.RETRIEVAL_DOCUMENT.value,
        )
        return response["embedding"]

    def embed_query(self, query: str) -> List[float]:
        response = self._genai.embed_content(
            model=self.model,
            content=query,
            task_type=TaskType.RETRIEVAL_QUERY.value,
        )
        return response["embedding"]


# ── Ollama ────────────────────────────────────────────────────────────────────

class OllamaEmbedder(BaseEmbedder):
    """Embeds via local Ollama server using its REST API (no extra SDK needed)."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        cfg = get_provider_config("ollama", category="embedder")
        model = model or cfg.default_model
        if not model:
            raise ValueError("Missing default model for ollama in clients config")
        super().__init__(model)
        self.base_url = (
            base_url
            or os.getenv(cfg.base_url_env or "", cfg.default_base_url or "")
        ).rstrip("/")

    def _embed(self, text: str) -> List[float]:
        payload = json.dumps({"model": self.model, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["embedding"]

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        return [self._embed(doc.content) for doc in documents]

    def embed_query(self, query: str) -> List[float]:
        return self._embed(query)


# ── OpenAI-compatible (OpenAI, Deepseek, Kimi) - config-driven ────────────────

class OpenAICompatibleEmbedder(BaseEmbedder):
    """
    Embeds via an OpenAI-compatible `/embeddings` REST endpoint.
    
    Supports: openai, deepseek, kimi (configuration-driven, no repetitive subclasses).
    """

    def __init__(
        self,
        provider: str,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize embedder for an OpenAI-compatible provider using config registry.
        
        Args:
            provider: "openai" | "deepseek" | "kimi"
            model: override default model
            api_key: API key (or read from env)
            base_url: base URL (or read from env)
        """
        config = get_provider_config(provider, category="embedder")
        model = model or config.default_model
        super().__init__(model)
        self.provider = provider
        self.api_key = api_key or os.getenv(config.api_key_env or "")
        self.base_url = (base_url or os.getenv(config.base_url_env or "", config.default_base_url or "")).rstrip("/")
        if not self.api_key and config.requires_api_key():
            raise ValueError(f"{config.api_key_env} is required for {provider}")

    def _embed_many(self, texts: List[str]) -> List[List[float]]:
        payload = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in data]

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        return self._embed_many([doc.content for doc in documents])

    def embed_query(self, query: str) -> List[float]:
        return self._embed_many([query])[0]


# ── HuggingFace (sentence-transformers) ──────────────────────────────────────

class HuggingFaceEmbedder(BaseEmbedder):
    """Embeds locally via sentence-transformers (pip install sentence-transformers)."""

    def __init__(self, model: str | None = None) -> None:
        cfg = get_provider_config("huggingface", category="embedder")
        model = model or cfg.default_model
        if not model:
            raise ValueError("Missing default model for huggingface in clients config")
        super().__init__(model)
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError("pip install sentence-transformers") from exc
        self._st = SentenceTransformer(model)

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        return self._st.encode([doc.content for doc in documents], convert_to_list=True)

    def embed_query(self, query: str) -> List[float]:
        return self._st.encode(query, convert_to_list=True)


# ── AWS Bedrock ───────────────────────────────────────────────────────────────

class BedrockEmbedder(BaseEmbedder):
    """Embeds via AWS Bedrock (boto3 must be installed and credentials configured)."""

    def __init__(
        self,
        model: str | None = None,
        region: str | None = None,
        profile: str = "default",
    ) -> None:
        cfg = get_provider_config("bedrock", category="embedder")
        model = model or cfg.default_model
        if not model:
            raise ValueError("Missing default model for bedrock in clients config")
        super().__init__(model)
        try:
            import boto3
            session = boto3.Session(
                profile_name=profile,
                region_name=region or os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            )
            self._client = session.client("bedrock-runtime")
        except ImportError as exc:
            raise ImportError("pip install boto3") from exc

    def _embed(self, text: str) -> List[float]:
        import json
        body = json.dumps({"inputText": text})
        resp = self._client.invoke_model(
            modelId=self.model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        return json.loads(resp["body"].read())["embedding"]

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        return [self._embed(doc.content) for doc in documents]

    def embed_query(self, query: str) -> List[float]:
        return self._embed(query)


# ── Factory ───────────────────────────────────────────────────────────────────

_PROVIDERS = {
    "gemini": GeminiEmbedder,
    "ollama": OllamaEmbedder,
    "openai": lambda **kwargs: OpenAICompatibleEmbedder("openai", **kwargs),
    "deepseek": lambda **kwargs: OpenAICompatibleEmbedder("deepseek", **kwargs),
    "kimi": lambda **kwargs: OpenAICompatibleEmbedder("kimi", **kwargs),
    "huggingface": HuggingFaceEmbedder,
    "bedrock": BedrockEmbedder,
}


def get_embedder(provider: str | None = None, model: str | None = None, **kwargs: Any) -> BaseEmbedder:
    """Return an embedder for *provider* (default: EMBEDDING_PROVIDER env / ollama).

    Args:
        provider: "ollama" | "gemini" | "openai" | "deepseek" | "kimi" | "huggingface" | "bedrock"
        model:    Override the default model for that provider.
        **kwargs: Passed to the provider constructor (e.g. api_key, base_url, region).
    """
    key = (provider or os.getenv("EMBEDDING_PROVIDER", "ollama")).strip().lower()
    cls = _PROVIDERS.get(key)
    if cls is None:
        raise ValueError(f"Unknown provider '{key}'. Choose from: {', '.join(_PROVIDERS)}")
    if model:
        kwargs["model"] = model
    return cls(**kwargs)
