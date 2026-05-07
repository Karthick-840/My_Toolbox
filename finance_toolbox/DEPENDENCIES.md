# finance_toolbox Dependency Policy

## Role
Finance domain package. Should remain independent from AI runtime layers.

## Allowed Imports
- my_toolbox
- Python standard library
- Finance/data libraries required for market workflows

## Forbidden Imports
- llm_toolbox
- ollama_toolbox
- agentic_toolbox

## Notes
- AI integration should be done via external adapters, not direct core imports.
- Preserve deterministic finance behavior regardless of model runtime availability.
