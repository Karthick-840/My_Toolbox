# agentic_toolbox Dependency Policy

## Role
Agent orchestration layer supporting both local and cloud runtimes.

## Allowed Imports
- llm_toolbox
- ollama_toolbox adapters
- my_toolbox
- Python standard library
- Agent orchestration libraries (Pydantic-AI, LangGraph)

## Forbidden Imports
- finance_toolbox core internals

## Required Responsibilities
- Runtime selection between local Ollama default and optional cloud providers.
- Hybrid orchestration support (Pydantic-AI and LangGraph).
- Coding assistant workflows should call llm_toolbox contracts instead of re-implementing provider logic.

## Notes
- Keep model/provider selection configurable per run.
