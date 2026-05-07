"""Bridge layer to interoperate with llm_toolbox and my_toolbox.

The adapter defaults to `backend="auto"`:
- prefers llm_toolbox native clients when available
- falls back to standalone LangChain providers otherwise
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .provider_factory import get_chat_model, supported_providers


@dataclass
class UnifiedToolboxLLM:
    """Unified chat interface for standalone + toolbox-integrated operation."""

    provider: str
    model: str | None = None
    backend: str = "auto"  # auto | llm_toolbox | langchain
    use_my_toolbox_logging: bool = False
    temperature: float = 0.2

    def __post_init__(self) -> None:
        if self.provider.strip().lower() not in supported_providers():
            raise ValueError(
                f"Unsupported provider '{self.provider}'. Choose from: {', '.join(supported_providers())}"
            )

    def invoke(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        """Invoke selected backend and return text response."""
        if self.backend in {"auto", "llm_toolbox"}:
            try:
                return self._invoke_llm_toolbox(prompt=prompt, system_prompt=system_prompt, **kwargs)
            except Exception:
                if self.backend == "llm_toolbox":
                    raise

        return self._invoke_langchain(prompt=prompt, system_prompt=system_prompt, **kwargs)

    def _invoke_langchain(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        chat_model = get_chat_model(
            provider=self.provider,
            model=self.model,
            temperature=kwargs.pop("temperature", self.temperature),
            **kwargs,
        )
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

    def _invoke_llm_toolbox(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        # Support both installed package imports and monorepo nested structure.
        try:
            from llm_toolbox.clients import ChatMessage, get_llm_client
        except ImportError:
            from llm_toolbox.llm_toolbox.clients import ChatMessage, get_llm_client

        provider = self.provider.strip().lower()
        if provider == "openai":
            # llm_toolbox currently reserves this provider but does not implement it.
            return self._invoke_langchain(prompt=prompt, system_prompt=system_prompt, **kwargs)

        client = get_llm_client(
            provider=provider,
            model=self.model,
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
        )

        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))

        call_fn = client.complete

        if self.use_my_toolbox_logging:
            call_fn = self._maybe_wrap_with_my_toolbox_logging(call_fn)

        return call_fn(messages=messages, temperature=kwargs.get("temperature", self.temperature))

    @staticmethod
    def _maybe_wrap_with_my_toolbox_logging(call_fn):
        try:
            from my_toolbox import log_calls
        except Exception:
            return call_fn

        @log_calls(logfile=None, console=True)
        def wrapped(*args, **kwargs):
            return call_fn(*args, **kwargs)

        return wrapped
