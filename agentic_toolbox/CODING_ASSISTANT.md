# Coding Assistant Usage

## Goal

Run a coding assistant with shared tools for file inspection, safe command execution, git status, diffs, compile checks, and basic validation.

## Local Ollama First

Start Ollama locally:

```sh
ollama serve
ollama pull gemma3:latest
```

Run the tool-enabled coding assistant from the repository root:

```sh
python - <<'PY'
from agentic_toolbox.coding_assistant_agent import run_tool_enabled_coding_assistant

response = run_tool_enabled_coding_assistant(
    user_prompt="Inspect the Python files in this repo and suggest how to structure a coding assistant package.",
    provider="ollama",
    model="gemma3:latest",
    workspace_root="/workspaces/My_Toolbox",
)
print(response)
PY
```

## Gemini Override

```sh
export GOOGLE_API_KEY="your-key"
python - <<'PY'
from agentic_toolbox.coding_assistant_agent import run_tool_enabled_coding_assistant

response = run_tool_enabled_coding_assistant(
    user_prompt="Read the repo structure and propose a FastAPI layout for AI tools.",
    provider="gemini",
    model="gemini-1.5-flash",
    workspace_root="/workspaces/My_Toolbox",
    gemini_api_key=None,
)
print(response)
PY
```

## Available Tool Surface

- `list_files`
- `read_file`
- `write_file`
- `run_command`
- `git_status`
- `git_diff`
- `run_pytest`
- `run_ruff`
- `compile_python`

## Notes

- Tool execution is workspace-bounded.
- Command execution is allow-listed to keep the coding assistant predictable.
- Shared code lives in `llm_toolbox/tools/coding_tools.py` so both local and cloud-backed agents can reuse the same tool layer.
