"""Helpers for building Pydantic-AI agents on local Ollama or Gemini."""

from __future__ import annotations

import os
from typing import Any


def build_pydantic_model(provider: str = "ollama", model: str | None = None, **kwargs: Any):
    """Return a Pydantic-AI model object for the requested provider."""

    provider_key = provider.strip().lower()

    if provider_key == "ollama":
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        base_url = kwargs.get("base_url", "http://localhost:11434/v1")
        return OpenAIModel(
            model_name=model or "gemma3:latest",
            provider=OpenAIProvider(base_url=base_url),
        )

    if provider_key == "gemini":
        from pydantic_ai.models.gemini import GeminiModel

        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini Pydantic-AI runtime")
        return GeminiModel(model or "gemini-1.5-flash", api_key=api_key)

    raise ValueError(f"Unsupported provider for Pydantic-AI runtime: {provider}")


def create_coding_agent(provider: str = "ollama", model: str | None = None, **kwargs: Any):
    """Build a minimal Pydantic-AI coding assistant agent."""

    from pydantic_ai import Agent

    system_prompt = kwargs.get(
        "system_prompt",
        "You are a precise coding assistant. Prefer minimal safe changes and runnable outputs.",
    )
    agent_model = build_pydantic_model(provider=provider, model=model, **kwargs)
    return Agent(model=agent_model, system_prompt=system_prompt)


def create_coding_agent_with_tools(
    provider: str = "ollama",
    model: str | None = None,
    workspace_root: str = ".",
    **kwargs: Any,
):
    """Build a Pydantic-AI coding assistant with reusable coding tools."""

    from pydantic_ai import Agent
    from llm_toolbox.tools import CodingTools

    system_prompt = kwargs.get(
        "system_prompt",
        "You are a precise coding assistant. Use the available tools to inspect files, run checks, and make safe coding decisions.",
    )
    agent_model = build_pydantic_model(provider=provider, model=model, **kwargs)
    toolset = CodingTools(workspace_root=workspace_root)
    agent = Agent(model=agent_model, system_prompt=system_prompt)

    @agent.tool_plain
    def list_files(pattern: str = "*.py", recursive: bool = True, limit: int = 200) -> list[str]:
        return toolset.list_files(pattern=pattern, recursive=recursive, limit=limit)

    @agent.tool_plain
    def read_file(path: str, max_chars: int = 12000) -> str:
        return toolset.read_file(path=path, max_chars=max_chars)

    @agent.tool_plain
    def write_file(path: str, content: str, backup: bool = True) -> str:
        return toolset.write_file(path=path, content=content, backup=backup)

    @agent.tool_plain
    def run_command(command: str, cwd: str = ".", timeout: int = 30) -> dict[str, Any]:
        return toolset.run_command(command=command, cwd=cwd, timeout=timeout).to_dict()

    @agent.tool_plain
    def git_status(repo_root: str = ".") -> str:
        return toolset.git_status(repo_root=repo_root)

    @agent.tool_plain
    def git_diff(repo_root: str = ".", path: str | None = None) -> str:
        return toolset.git_diff(repo_root=repo_root, path=path)

    @agent.tool_plain
    def run_pytest(target: str = ".", cwd: str = ".", timeout: int = 120) -> dict[str, Any]:
        return toolset.run_pytest(target=target, cwd=cwd, timeout=timeout)

    @agent.tool_plain
    def run_ruff(target: str = ".", cwd: str = ".", timeout: int = 120) -> dict[str, Any]:
        return toolset.run_ruff(target=target, cwd=cwd, timeout=timeout)

    @agent.tool_plain
    def compile_python(target: str, cwd: str = ".", timeout: int = 60) -> dict[str, Any]:
        return toolset.compile_python(target=target, cwd=cwd, timeout=timeout)

    return agent