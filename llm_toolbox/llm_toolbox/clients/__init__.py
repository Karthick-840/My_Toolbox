"""Shared LLM adapter layer — provider-agnostic chat clients.

Core abstractions
-----------------
ChatMessage         Data container (role, content)
BaseLLMClient       ABC: .complete(), .stream()

Factory
-------
get_llm_client()    Routes to Ollama, Gemini, Groq, Deepseek, Kimi, GitHub Models

Clients
-------
OllamaLLMClient     (local, open-source)
GeminiLLMClient     (Google's Gemini)
GroqLLMClient       (Groq's LPU)
DeepseekLLMClient   (Deepseek's models)
KimiLLMClient       (Kimi/Moonshot - Chinese LLM)
GitHub Models       (OpenAI-compatible endpoint at models.github.ai)

Usage
-----
from llm_toolbox.clients import ChatMessage, BaseLLMClient, get_llm_client

client = get_llm_client("ollama", model="llama3.2:latest")
msg = ChatMessage(role="user", content="Hello!")
answer = client.complete([msg])
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Any, Iterable, List, Optional

if TYPE_CHECKING:
    pass  # avoid circular imports


# ── Provider Config (single source in clients package) ───────────────────────

PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    "ollama": {
        "aliases": [],
        "model": {"env": "OLLAMA_MODEL", "default": "llama3.2:1b"},
        "endpoint": {"env": "OLLAMA_BASE_URL", "default": "http://localhost:11434"},
        "infer": {
            "model_prefixes": [],
            "endpoint_markers": ["localhost:11434", "127.0.0.1:11434"],
        },
        "client": {
            "module": "llm_toolbox.clients.ollama_client",
            "class": "OllamaLLMClient",
            "fields": {
                "base_url": {
                    "kwarg": "base_url",
                    "use_provider_endpoint_default": True,
                }
            },
        },
    },
    "gemini": {
        "aliases": [],
        "model": {"env": "GEMINI_MODEL", "default": "gemini-1.5-flash"},
        "endpoint": {"env": None, "default": None},
        "infer": {"model_prefixes": ["gemini"], "endpoint_markers": []},
        "client": {
            "module": "llm_toolbox.clients.gemini_client",
            "class": "GeminiLLMClient",
            "fields": {"api_key": {"kwarg": "api_key"}},
        },
    },
    "groq": {
        "aliases": [],
        "model": {"env": "GROQ_MODEL", "default": "mixtral-8x7b-32768"},
        "endpoint": {"env": None, "default": None},
        "infer": {"model_prefixes": ["mixtral", "llama-3"], "endpoint_markers": []},
        "client": {
            "module": "llm_toolbox.clients.groq_client",
            "class": "GroqLLMClient",
            "fields": {"api_key": {"kwarg": "api_key"}},
        },
    },
    "deepseek": {
        "aliases": [],
        "model": {"env": "DEEPSEEK_MODEL", "default": "deepseek-chat"},
        "endpoint": {"env": "DEEPSEEK_BASE_URL", "default": "https://api.deepseek.com/v1"},
        "infer": {
            "model_prefixes": ["deepseek"],
            "endpoint_markers": ["api.deepseek.com"],
        },
        "client": {
            "module": "llm_toolbox.clients.deepseek_client",
            "class": "DeepseekLLMClient",
            "fields": {
                "api_key": {"kwarg": "api_key"},
                "base_url": {
                    "kwarg": "base_url",
                    "use_provider_endpoint_default": True,
                },
            },
        },
    },
    "kimi": {
        "aliases": [],
        "model": {"env": "KIMI_MODEL", "default": "moonshot-v1-8k"},
        "endpoint": {"env": "KIMI_BASE_URL", "default": "https://api.moonshot.cn/v1"},
        "infer": {
            "model_prefixes": ["moonshot", "kimi"],
            "endpoint_markers": ["api.moonshot.cn"],
        },
        "client": {
            "module": "llm_toolbox.clients.kimi_client",
            "class": "KimiLLMClient",
            "fields": {
                "api_key": {"kwarg": "api_key"},
                "base_url": {
                    "kwarg": "base_url",
                    "use_provider_endpoint_default": True,
                },
            },
        },
    },
    "github": {
        "aliases": ["github_models"],
        "model": {"env": "GITHUB_MODEL", "default": "openai/gpt-4.1-mini"},
        "endpoint": {"env": "GITHUB_BASE_URL", "default": "https://models.github.ai/inference"},
        "infer": {
            "model_prefixes": ["openai/", "gpt-"],
            "endpoint_markers": ["models.github.ai"],
        },
        "client": {
            "module": "llm_toolbox.clients.deepseek_client",
            "class": "DeepseekLLMClient",
            "fields": {
                "api_key": {"kwarg": "api_key", "env": "GITHUB_TOKEN"},
                "base_url": {
                    "kwarg": "base_url",
                    "use_provider_endpoint_default": True,
                },
            },
            "provider_override": "github",
        },
    },
}

SUPPORTED_PROVIDERS = tuple(PROVIDER_REGISTRY.keys())

_PROVIDER_ALIAS_MAP = {
    alias: provider
    for provider, cfg in PROVIDER_REGISTRY.items()
    for alias in [provider, *cfg.get("aliases", [])]
}


@dataclass
class ProviderConfig:
    """Unified provider metadata for embedder/chat configuration lookups."""

    name: str
    category: str
    sdk_name: str | None = None
    api_key_env: str | None = None
    base_url_env: str | None = None
    default_base_url: str | None = None
    default_model: str | None = None
    local: bool = False
    import_path: str | None = None
    class_name: str | None = None

    def requires_api_key(self) -> bool:
        return self.api_key_env is not None and not self.local


EMBEDDER_REGISTRY: dict[str, ProviderConfig] = {
    "ollama": ProviderConfig(
        name="ollama",
        category="embedder",
        local=True,
        base_url_env="OLLAMA_BASE_URL",
        default_base_url="http://localhost:11434",
        default_model="nomic-embed-text",
    ),
    "gemini": ProviderConfig(
        name="gemini",
        category="embedder",
        sdk_name="google-generativeai",
        api_key_env="GOOGLE_API_KEY",
        default_model="models/embedding-001",
        import_path="google.generativeai",
    ),
    "openai": ProviderConfig(
        name="openai",
        category="embedder",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        default_base_url="https://api.openai.com/v1",
        default_model="text-embedding-3-small",
        class_name="OpenAICompatibleEmbedder",
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        category="embedder",
        api_key_env="DEEPSEEK_API_KEY",
        base_url_env="DEEPSEEK_BASE_URL",
        default_base_url="https://api.deepseek.com/v1",
        default_model="deepseek-embedding",
        class_name="OpenAICompatibleEmbedder",
    ),
    "kimi": ProviderConfig(
        name="kimi",
        category="embedder",
        api_key_env="KIMI_API_KEY",
        base_url_env="KIMI_BASE_URL",
        default_base_url="https://api.moonshot.cn/v1",
        default_model="text-embedding-v1",
        class_name="OpenAICompatibleEmbedder",
    ),
    "huggingface": ProviderConfig(
        name="huggingface",
        category="embedder",
        sdk_name="sentence-transformers",
        local=True,
        default_model="sentence-transformers/all-MiniLM-L6-v2",
    ),
    "bedrock": ProviderConfig(
        name="bedrock",
        category="embedder",
        sdk_name="boto3",
        default_model="amazon.titan-embed-text-v1",
    ),
}


def get_provider_config(provider: str, category: str = "chat") -> ProviderConfig:
    """Return provider config for embedder/chat lookups."""
    key = normalize_provider_name(provider)
    if category == "embedder":
        cfg = EMBEDDER_REGISTRY.get(key)
        if cfg is None:
            available = ", ".join(EMBEDDER_REGISTRY.keys())
            raise ValueError(f"Unknown embedder provider '{provider}'. Choose from: {available}")
        return cfg

    if category == "chat":
        cfg = PROVIDER_REGISTRY.get(key)
        if cfg is None:
            available = ", ".join(PROVIDER_REGISTRY.keys())
            raise ValueError(f"Unknown chat provider '{provider}'. Choose from: {available}")
        model_cfg = cfg.get("model", {})
        endpoint_cfg = cfg.get("endpoint", {})
        fields = cfg.get("client", {}).get("fields", {})
        api_field = fields.get("api_key", {})
        return ProviderConfig(
            name=key,
            category="chat",
            api_key_env=api_field.get("env") or f"{key.upper()}_API_KEY",
            base_url_env=endpoint_cfg.get("env"),
            default_base_url=endpoint_cfg.get("default"),
            default_model=model_cfg.get("default"),
        )

    raise ValueError("category must be either 'embedder' or 'chat'")


def list_providers(category: str = "chat") -> list[str]:
    """Return available providers for the selected category."""
    if category == "embedder":
        return list(EMBEDDER_REGISTRY.keys())
    if category == "chat":
        return list(PROVIDER_REGISTRY.keys())
    raise ValueError("category must be either 'embedder' or 'chat'")


def normalize_provider_name(provider: str) -> str:
    key = provider.strip().lower()
    return _PROVIDER_ALIAS_MAP.get(key, key)


def default_model_for_provider(provider: str) -> str:
    key = normalize_provider_name(provider)
    cfg = PROVIDER_REGISTRY.get(key, PROVIDER_REGISTRY["ollama"])
    model_cfg = cfg.get("model", {})
    env_key = model_cfg.get("env")
    if env_key:
        val = os.getenv(env_key)
        if val:
            return val
    return model_cfg.get("default", PROVIDER_REGISTRY["ollama"]["model"]["default"])


def default_endpoint_for_provider(provider: str) -> str | None:
    key = normalize_provider_name(provider)
    cfg = PROVIDER_REGISTRY.get(key, {})
    endpoint_cfg = cfg.get("endpoint", {})
    env_key = endpoint_cfg.get("env")
    default = endpoint_cfg.get("default")
    if env_key:
        return os.getenv(env_key, default)
    return default


def _load_client_class(module_name: str, class_name: str):
    module = import_module(module_name)
    return getattr(module, class_name)


def _build_provider_init_kwargs(provider_key: str, model: str | None, runtime_kwargs: dict[str, Any]) -> dict[str, Any]:
    spec = PROVIDER_REGISTRY[provider_key]["client"]
    init_kwargs: dict[str, Any] = {
        "model": model or default_model_for_provider(provider_key),
    }
    for field_name, field_spec in spec.get("fields", {}).items():
        value = runtime_kwargs.get(field_spec["kwarg"])
        if value is None and field_spec.get("env"):
            value = os.getenv(field_spec["env"])
        if value is None and field_spec.get("use_provider_endpoint_default"):
            value = default_endpoint_for_provider(provider_key)
        if value is not None:
            init_kwargs[field_name] = value
    return init_kwargs


def infer_provider_from_model(model: str) -> str:
    key = model.lower()
    for provider, cfg in PROVIDER_REGISTRY.items():
        for prefix in cfg.get("infer", {}).get("model_prefixes", []):
            if key.startswith(prefix):
                return provider
    return "ollama"


def infer_provider_from_endpoint(endpoint: str | None, fallback: str = "ollama") -> str:
    if not endpoint:
        return fallback
    ep = endpoint.strip().lower()
    for provider, cfg in PROVIDER_REGISTRY.items():
        for marker in cfg.get("infer", {}).get("endpoint_markers", []):
            if marker in ep:
                return provider
    return fallback


def resolve_chat_provider(*, model: str, endpoint: str | None = None, provider: str | None = None) -> str:
    if provider and provider.strip():
        return normalize_provider_name(provider)
    return infer_provider_from_endpoint(endpoint, infer_provider_from_model(model))


# ── Core abstractions ──────────────────────────────────────────────────────────

@dataclass
class ChatMessage:
    """Provider-neutral chat message."""

    role: str
    content: str


class BaseLLMClient(ABC):
    """Common interface used by llm, ollama, and agentic toolboxes."""

    provider: str
    model: str

    @abstractmethod
    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        """Return a full non-streaming completion."""

    def stream(self, messages: List[ChatMessage], temperature: float = 0.2) -> Iterable[str]:
        """Optional streaming output; default falls back to complete()."""
        yield self.complete(messages=messages, temperature=temperature)

    def system_user_messages(self, system_prompt: Optional[str], user_prompt: str) -> List[ChatMessage]:
        output: List[ChatMessage] = []
        if system_prompt:
            output.append(ChatMessage(role="system", content=system_prompt))
        output.append(ChatMessage(role="user", content=user_prompt))
        return output


# ── Factory ────────────────────────────────────────────────────────────────────

def get_llm_client(provider: str, model: str | None = None, **kwargs: Any) -> BaseLLMClient:
    """Get an LLM client for *provider* with optional *model* override.

    Args:
        provider: "ollama" | "gemini" | "groq" | "deepseek" | "kimi" | "github"
        model:    Model name (e.g., "llama3.2:latest", "gemini-1.5-flash")
        **kwargs: Provider-specific args (api_key, base_url, region, etc.)

    Returns:
        An instance of BaseLLMClient (OllamaLLMClient, GeminiLLMClient, etc.)

    Usage:
        client = get_llm_client("ollama", model="llama3.2:latest")
        resp = client.complete([ChatMessage(role="user", content="Hi")])
    """
    key = normalize_provider_name(provider)
    if key == "openai":
        raise NotImplementedError("OpenAI adapter is planned; provider slot reserved")

    provider_cfg = PROVIDER_REGISTRY.get(key)
    if provider_cfg:
        spec = provider_cfg["client"]
        client_cls = _load_client_class(spec["module"], spec["class"])
        init_kwargs = _build_provider_init_kwargs(key, model, kwargs)
        client = client_cls(**init_kwargs)
        provider_override = spec.get("provider_override")
        if provider_override:
            client.provider = provider_override
        return client

    raise ValueError(f"Unsupported provider: {provider}. Choose from: {', '.join(SUPPORTED_PROVIDERS)}")


# ── Public API ─────────────────────────────────────────────────────────────────

__all__ = [
    "ChatMessage",
    "BaseLLMClient",
    "ProviderConfig",
    "PROVIDER_REGISTRY",
    "EMBEDDER_REGISTRY",
    "get_provider_config",
    "list_providers",
    "get_llm_client",
    "SUPPORTED_PROVIDERS",
    "normalize_provider_name",
    "default_model_for_provider",
    "default_endpoint_for_provider",
    "infer_provider_from_model",
    "infer_provider_from_endpoint",
    "resolve_chat_provider",
]

