"""Compatibility shim for older imports.

Use provider_factory.py as the source of truth.
"""

from __future__ import annotations

from .provider_factory import get_chat_model, get_provider_defaults, supported_providers

SUPPORTED_CHAT_PROVIDERS = supported_providers()
DEFAULT_CHAT_MODELS = {
    provider: get_provider_defaults(provider).chat_model for provider in SUPPORTED_CHAT_PROVIDERS
}


def chat_once(
    prompt: str,
    *,
    provider: str,
    model: str | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    **kwargs,
) -> str:
    """Single-turn chat helper retained for backward compatibility."""
    from langchain_core.messages import HumanMessage, SystemMessage

    chat_model = get_chat_model(provider=provider, model=model, temperature=temperature, **kwargs)
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    response = chat_model.invoke(messages)
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part) for part in content)
    return str(content)
