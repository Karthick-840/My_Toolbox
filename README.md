# My Toolbox

A Python utility package with helper modules for:

- API operations
- PDF extraction and manipulation
- Date and string operations
- GCP storage and sheets utilities
- Streamlit helper components
- Logging and decorator helpers

## Installation

Install from source:

```bash
pip install .
```

Install in editable mode for development:

```bash
pip install -e .
```

Install from GitHub:

```bash
pip install "git+https://github.com/Karthick-840/My_Toolbox.git@main"
```

Install from local wheel (best for stable reuse):

```bash
pip install dist/my_toolbox-1.1.0-py3-none-any.whl
```

## uv Installation

If your target project uses uv:

```bash
uv add /absolute/path/to/My_Toolbox
```

Editable mode while co-developing both repositories:

```bash
uv add --editable /absolute/path/to/My_Toolbox
```

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
python -m build
```

Artifacts are generated in the `dist/` directory.

This repository now uses [pyproject.toml](pyproject.toml) as the package source of truth.

For full packaging and release steps, see [docs/Package_Preparation.md](docs/Package_Preparation.md).

For branch gatekeeping and required CI checks, see [docs/GitHub_Actions_Gatekeeper.md](docs/GitHub_Actions_Gatekeeper.md).

## Module Notes

- `my_toolbox.pdf_tools`: PDF read/write, merge, split, extraction helpers.
- `my_toolbox.streamlit_tools`: Multi-app and menu helpers for Streamlit.
- `my_toolbox.gcp_tools`: Google Sheets and Cloud Storage helpers.

Some modules require external services or credentials (for example, GCP credentials and Streamlit runtime).

## Development

```bash
pip install -r requirements.txt
```

Run a basic import smoke test:

```bash
python -c "import my_toolbox"
```

## License

MIT
