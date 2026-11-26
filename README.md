# My Toolbox

A Python utility package with helper modules for:

- API operations
- PDF extraction and manipulation
- Date and string operations
- GCP storage and sheets utilities
- Streamlit helper components
- Logging and decorator helpers

## Installation

Using uv (recommended):

```bash
uv add "my-toolbox @ git+https://github.com/Karthick-840/My_Toolbox.git"            # core only
uv add "my-toolbox[documents,web] @ git+https://github.com/Karthick-840/My_Toolbox.git"  # with extras
uv add --editable /absolute/path/to/My_Toolbox                                     # co-developing
```

Using pip:

```bash
pip install "git+https://github.com/Karthick-840/My_Toolbox.git@main"
pip install "my_toolbox[all] @ git+https://github.com/Karthick-840/My_Toolbox.git@main"
```

Python 3.11-3.13 is supported.

## Quick Start

```python
from my_toolbox import log_calls, run_if, requires

@log_calls(logfile=None)
@run_if(lambda: True)
@requires(lambda: True)
def hello(name):
    return f"Hello {name}"

print(hello("World"))
```

## Build Distributions

```bash
uv build        # or: make build
```

Artifacts are generated in the `dist/` directory. [pyproject.toml](pyproject.toml) is the single source of truth for the package; `uv.lock` pins the exact versions used for development, tests and CI.

For branch gatekeeping and required CI checks, see [docs/GitHub_Actions_Gatekeeper.md](docs/GitHub_Actions_Gatekeeper.md).

## Module Notes

- `my_toolbox.core`: `my_decorators`, `log_tools`, `string_ops`, `time_ops`, `validation`, `error_handling`, `operator_tools` (base install).
- `my_toolbox.cloud`: `gcp_tools` (Sheets, Storage, BigQuery) - `pip install "my-toolbox[cloud]"`.
- `my_toolbox.data`: `postgress_tools`, `kaggle_tools`, `directory_tools`, `excel_tools`, `mongo_tools`, `visualization_tools` - `[data]`.
- `my_toolbox.documents`: `pdf_tools` (PDF read/merge/split/extract, `PDF_FromImages` for images -> PDF, `PDF_Security`) - `[documents]`; `image_tools` (viewer, background removal) - `[images]`.
- `my_toolbox.web`: `api_tools`, `notion_tools`, `streamlit_tools`, `calendar_tools`, `email_tools`, `medium_tools` (notebook -> Medium draft; needs `MEDIUM_TOKEN`) - `[web]`.
- `my_toolbox.devops`: `git_tools`, `project_ops`.
- `my_toolbox.mcp`: MCP server for PDF operations and notebook -> Medium - `[mcp]`.

Install everything with the `[all]` extra.

### Related toolboxes (separate packages, not part of `my_toolbox`)

Finance, LLM, LangChain and agentic/MCP work live in their own repos next to this one: `Finance_Toolbox`, `LLM_Toolbox_v2`, `LangChain_Toolbox`, `Agentic_Toolbox`. They depend on `my-toolbox`, never the other way round.
 Example: `from my_toolbox.core.time_ops import DateFunctions`.

Some modules require external services or credentials (for example, GCP credentials and Streamlit runtime).

## Dependencies: production vs development

- **Production** (what consumers get): `[project.dependencies]` (core) and `[project.optional-dependencies]` (`cloud`, `data`, `documents`, `web`, `all`).
- **Development** (never shipped): `[dependency-groups]` in `pyproject.toml` - `test`, `lint`, `audit`, `release`, `app`, and `dev` (all of them, synced by default).
- There is no `requirements.txt`. If a deployment target needs one: `make export-prod`.

## Development

```bash
uv sync --all-extras      # create .venv with every extra + the dev group (make install)
make test                 # uv run --all-extras pytest
make ruff                 # lint
```

## PDF Operations app

A local browser app (not part of the installed package) lives in [`app/`](app/). It exposes everything in `my_toolbox.documents.pdf_tools` - extract text/images/tables, merge, split, combine, rename, remove empty PDFs, text to PDF, and Snap to PDF (paste screenshots with Ctrl+V).

```bash
make app     # uv run --extra documents --group app python -m app.pdf_app
```

Opens http://127.0.0.1:5050. Files are stored in `./workspace/inputs` and `./workspace/outputs` (override with `PDF_APP_WORKSPACE`). Table extraction needs Java (tabula-py).

## MCP server and skills

```bash
pip install "my-toolbox[mcp] @ git+https://github.com/Karthick-840/My_Toolbox.git@v1.2.0"
my-toolbox-mcp --workspace /data/work     # stdio; files in <workspace>/inputs and /outputs
```

Usage guides for agents and humans live in [`skills/`](skills/): `use-my-toolbox` (library) and `use-my-toolbox-mcp` (server, client config, Ansible install). Roadmap (not implemented): interactive PDF editing, LLM-based PDF chat, auto-tagging.

## License

MIT
