# ollama_toolbox Dependency Policy

## Role
Local runtime toolbox for Ollama-specific chat, RAG, and tool-calling behavior.

## Allowed Imports
- my_toolbox
- llm_toolbox shared contracts and adapters
- Python standard library
- Ollama-specific libraries

## Forbidden Imports
- finance_toolbox
- agentic_toolbox internals

## Required Responsibilities
- Keep Ollama-specific adapters and local runtime wrappers.
- Reuse shared embedding/query/index code from llm_toolbox (no duplication).

## Notes
- Existing duplicate files should remain compatibility wrappers until migration completes.
