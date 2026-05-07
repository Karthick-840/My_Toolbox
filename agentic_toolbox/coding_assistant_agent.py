"""First coding assistant entrypoint with local-first runtime and Gemini fallback."""

from __future__ import annotations

from agentic_toolbox.runtime_selector import AgenticRuntime, RuntimeConfig
from agentic_toolbox.pydantic_ai_runtime import create_coding_agent_with_tools

DEFAULT_SYSTEM_PROMPT = (
    "You are a precise coding assistant. "
    "Prefer safe edits, explain assumptions, and return runnable code."
)


def run_coding_assistant(
    user_prompt: str,
    provider: str = "ollama",
    model: str | None = None,
    gemini_api_key: str | None = None,
) -> str:
    if provider == "ollama":
        cfg = RuntimeConfig(provider="ollama", model=model or "gemma3:latest")
    elif provider == "gemini":
        cfg = RuntimeConfig(provider="gemini", model=model or "gemini-1.5-flash", gemini_api_key=gemini_api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    runtime = AgenticRuntime(cfg)
    return runtime.ask(user_prompt=user_prompt, system_prompt=DEFAULT_SYSTEM_PROMPT)


def run_tool_enabled_coding_assistant(
    user_prompt: str,
    provider: str = "ollama",
    model: str | None = None,
    workspace_root: str = ".",
    gemini_api_key: str | None = None,
) -> str:
    """Run the coding assistant through a Pydantic-AI agent with coding tools."""

    kwargs = {"workspace_root": workspace_root}
    if provider == "gemini" and gemini_api_key:
        kwargs["api_key"] = gemini_api_key

    agent = create_coding_agent_with_tools(
        provider=provider,
        model=model,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        **kwargs,
    )
    result = agent.run_sync(user_prompt)
    return getattr(result, "data", result)
