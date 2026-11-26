# my_toolbox Dependency Policy

## Role
Core utilities package used by all other toolboxes.

## Allowed Imports
- Python standard library
- External utility libraries needed by core helpers

## Forbidden Imports
- finance_toolbox
- llm_toolbox
- ollama_toolbox
- agentic_toolbox

## Notes
- Keep this toolbox lightweight and stable.
- Public exports in __init__.py are treated as long-lived API contracts.
