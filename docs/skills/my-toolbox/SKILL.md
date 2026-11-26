---
name: my-toolbox
description: Install and use the my_toolbox Python package (PDF, data, web, cloud, devops helpers) as a library, and run its MCP server (tools, resources, prompts) from an MCP client or Ansible.
---

# my-toolbox

## Part 1: Use as a library

### Install (pick extras you need)
```bash
pip install "my-toolbox @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
pip install "my-toolbox[documents,data] @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
```
Extras: `cloud`, `data`, `documents`, `web`, `images`, `mcp`, `all`. Base install is light; each subpackage imports only its own extra.
Dev: `uv sync` (uses `uv.lock`; no requirements.txt).

### Module map
| Package | Modules |
|---|---|
| `my_toolbox.core` | `validation`, `error_handling`, `operator_tools` |
| `my_toolbox.cloud` | cloud helpers (extra `cloud`) |
| `my_toolbox.data` | `mongo_tools`, `excel_tools`, `visualization_tools` (extra `data`) |
| `my_toolbox.documents` | `pdf_tools`, `image_tools` (extras `documents`, `images`) |
| `my_toolbox.web` | `calendar_tools`, `email_tools`, `medium_tools`, `streamlit_tools` (extra `web`) |
| `my_toolbox.devops` | `project_ops` |
| `my_toolbox.mcp` | MCP server (extra `mcp`), see Part 2 |

### PDF example
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

### Jupyter to Medium
```python
from my_toolbox.web.medium_tools import MediumPublisher
MediumPublisher(token="...").publish_notebook("analysis.ipynb", tags=["python"], status="draft")
```
Token falls back to env `MEDIUM_TOKEN`. Drafts by default.

### Local PDF web app
```bash
make app    # uv run --extra documents --group app python -m app.pdf_app
```
Workspace via `PDF_APP_WORKSPACE` (default `./workspace`). Opens http://127.0.0.1:5050, local only.

### Dev commands
`uv run pytest`, `uv run ruff check my_toolbox app tests`. Main is protected: use a PR; CI needs lint-and-test (3.11-3.13), build-and-verify and dependency-audit.

## Part 2: Use the MCP server

### Install
```bash
pip install "my-toolbox[mcp] @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
```
Pin a tag. Python 3.11-3.13. `extract_tables` needs Java (tabula); `images_to_pdf` needs the `images` extra.

### Run
```bash
my-toolbox-mcp --workspace /data/work     # stdio (default)
```
Workspace = `MY_TOOLBOX_WORKSPACE` env or `--workspace` (default `./workspace`):
- `inputs/` - put source files here
- `outputs/` - results are written here

All tool arguments are **bare file names** from `inputs/`. Paths, `..` and subfolders are rejected.

### Client config (Claude Desktop / VS Code / Copilot CLI style)
```json
{
  "mcpServers": {
    "my-toolbox": {
      "command": "my-toolbox-mcp",
      "args": ["--workspace", "/data/work"],
      "env": {"MEDIUM_TOKEN": "<only for notebook_to_medium>"}
    }
  }
}
```

### Tools
| Tool | Purpose |
|---|---|
| `list_files` | List `inputs/` and `outputs/` |
| `extract_text(file, page?, pattern?)` | Text, one page, or regex matches |
| `extract_pages(file, ranges, output_name?)` | Ranges like `3-7,10,12-` |
| `merge_pdfs(files, output_name)` | Merge in the given order |
| `split_pdf(file)` | One PDF per page |
| `remove_blank_pages(file, text_only?)` | Drop blank pages |
| `images_to_pdf(images, output_name)` | Images to one PDF |
| `write_text_pdf(output_name, content)` | Plain text to PDF |
| `notebook_to_medium(notebook, title?, tags?, status?)` | Draft post; needs `MEDIUM_TOKEN` |

### Resources and prompts
Resources (read-only context): `toolbox://files/inputs`, `toolbox://files/outputs`, `toolbox://pdf/{file}/info` (pages, encrypted, needs_ocr), `toolbox://guide`.
Prompts (templates): `summarize_pdf(file)`, `extract_section(file, topic)`, `clean_scan(file)`, `publish_notebook(notebook, tags)`.

### Typical flow
1. Copy files into `inputs/`.
2. `list_files`, then call the operation.
3. Read results from `outputs/<name>`.

### Ansible
```yaml
- name: Install my-toolbox MCP
  ansible.builtin.pip:
    name: "my-toolbox[mcp] @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
    virtualenv: /opt/my-toolbox
    virtualenv_command: python3 -m venv
```
Binary: `/opt/my-toolbox/bin/my-toolbox-mcp`.
