---
name: use-my-toolbox
description: Install and use the my_toolbox Python package (core, cloud, data, documents, web, devops) as a library, including the local PDF app and Medium publisher.
---

# Use my_toolbox as a library

## Install (pick extras you need)
```bash
pip install "my-toolbox @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
pip install "my-toolbox[documents,data] @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
```
Extras: `cloud`, `data`, `documents`, `web`, `images`, `mcp`, `all`. Base install is light; each subpackage imports only its own extra.
Dev: `uv sync` (uses `uv.lock`; no requirements.txt).

## Module map
| Package | Modules |
|---|---|
| `my_toolbox.core` | `validation`, `error_handling`, `operator_tools` |
| `my_toolbox.cloud` | cloud helpers (extra `cloud`) |
| `my_toolbox.data` | `mongo_tools`, `excel_tools`, `visualization_tools` (extra `data`) |
| `my_toolbox.documents` | `pdf_tools`, `image_tools` (extras `documents`, `images`) |
| `my_toolbox.web` | `calendar_tools`, `email_tools`, `medium_tools`, `streamlit_tools` (extra `web`) |
| `my_toolbox.devops` | `project_ops` |
| `my_toolbox.mcp` | MCP server (extra `mcp`), see skill `use-my-toolbox-mcp` |

## PDF example
```python
from my_toolbox.documents.pdf_tools import PDF_Extract, PDF_Manipulate, PDF_FromImages

m = PDF_Manipulate(input_path="inputs", output_path="outputs")
m.merge_pdfs(merge_dict=["a.pdf", "b.pdf"], output_file_name="both")
m.extract_pages("both.pdf", "1-3,5")
path, removed = m.remove_blank_pages("scan.pdf")
text = PDF_Extract("inputs", "outputs").complete_text_extract("a.pdf")
PDF_FromImages("inputs", "outputs").images_to_pdf(["inputs/p1.png", "inputs/p2.png"], "album.pdf")
```
Other classes: `PDFAccess`, `PDF_Security` (encryption check, password vault).

## Jupyter to Medium
```python
from my_toolbox.web.medium_tools import MediumPublisher
MediumPublisher(token="...").publish_notebook("analysis.ipynb", tags=["python"], status="draft")
```
Token falls back to env `MEDIUM_TOKEN`. Drafts by default.

## Local PDF web app
```bash
make app    # uv run --extra documents --group app python -m app.pdf_app
```
Workspace via `PDF_APP_WORKSPACE` (default `./workspace`). Opens http://127.0.0.1:5050, local only.

## Dev commands
`uv run pytest`, `uv run ruff check my_toolbox app tests`. Main is protected: use a PR; CI needs lint-and-test (3.11-3.13), build-and-verify and dependency-audit.
