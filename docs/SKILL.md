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
Extras: `cloud`, `data`, `analytics` (pandas/pyarrow/SQLAlchemy), `notebooks`, `documents`, `web`, `images`, `mcp`, `all`. Base install is light; each subpackage imports only its own extra.
Dev: `uv sync` (uses `uv.lock`; no requirements.txt).

### Module map
| Package | Modules |
|---|---|
| `my_toolbox.core` | `validation`, `error_handling`, `operator_tools`, `pipeline` (retry, PipelineRun, Checkpoint), `sql_guard` |
| `my_toolbox.cloud` | `gcp_tools`, `warehouse` (`BigQueryWarehouse`) (extra `cloud`) |
| `my_toolbox.data` | `mongo_tools`, `excel_tools`, `visualization_tools`, `quality` (profile, schema compare, quality issues, contracts, Parquet), `sql_tools` (`SQLClient`) (extras `data`, `analytics`) |
| `my_toolbox.documents` | `pdf_tools`, `image_tools` (extras `documents`, `images`) |
| `my_toolbox.web` | `calendar_tools`, `email_tools`, `medium_tools`, `streamlit_tools` (extra `web`) |
| `my_toolbox.devops` | `project_ops`, `notebook_tools` (strip outputs, secret scan, headless run; extra `notebooks`) |
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

#### Data engineering example
```python
from my_toolbox.data.quality import read_table, profile, quality_issues, check_contract, to_parquet
from my_toolbox.data.sql_tools import SQLClient
from my_toolbox.core.pipeline import retry, PipelineRun, Checkpoint

df = read_table("sales.csv")
print(profile(df)["column_profile"], quality_issues(df))
print(check_contract(df, {"columns": {"id": {"unique": True, "nullable": False}}, "min_rows": 1}))
to_parquet("sales.csv", "sales.parquet")

with SQLClient() as db:                      # DATABASE_URL env; read-only by default
    top = db.query("select * from orders", max_rows=100)
with SQLClient(read_only=False) as db:
    db.load(df, "sales_raw", if_exists="replace")

@retry(attempts=4, delay=1)                  # exponential backoff
def fetch(): ...

run, cp = PipelineRun("etl"), Checkpoint(".state.json")
with run.step("load") as step:
    step["rows"] = len(df)
cp.run_once("load", lambda: None)            # skipped on rerun
print(run.summary())
```
`BigQueryWarehouse` (`my_toolbox.cloud.warehouse`) has the same `query`/`load` shape.

Notebook hygiene: `notebook_tools.strip_outputs(path)`, `find_secrets(path)`, `run_notebook(src, out, parameters={"n": 5})`.

## Jupyter to Medium
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
Pin a tag. Python 3.11-3.13. The `mcp` extra includes `documents` and `analytics`. `extract_tables` needs Java (tabula); `images_to_pdf` needs the `images` extra.

### Run
```bash
my-toolbox-mcp --workspace /data/work     # stdio, read-only
my-toolbox-mcp --workspace /data/work --allow-write    # also enable [write] tools
```
Safety defaults: **read-only**. Tools marked `[write]` raise an error unless `--allow-write` (or `MY_TOOLBOX_ALLOW_WRITE=1`). Responses are capped at `MY_TOOLBOX_MAX_ROWS` (default 1000; `--max-rows`) and inputs over `MY_TOOLBOX_MAX_BYTES` (default 50 MB) are refused. `query_sql` uses `DATABASE_URL`, accepts one SELECT/WITH only, and never writes.
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
| `extract_pages(file, ranges, output_name?)` | [write] Ranges like `3-7,10,12-` |
| `merge_pdfs(files, output_name)` | [write] Merge in the given order |
| `split_pdf(file)` | [write] One PDF per page |
| `remove_blank_pages(file, text_only?)` | [write] Drop blank pages |
| `images_to_pdf(images, output_name)` | [write] Images to one PDF |
| `write_text_pdf(output_name, content)` | [write] Plain text to PDF |
| `notebook_to_medium(notebook, title?, tags?, status?)` | [write] Draft post; needs `MEDIUM_TOKEN` |
| `profile_data(file, sample_rows?)` | CSV/TSV/Parquet/JSON/Excel profile |
| `data_schema(file)` / `compare_data_schemas(a, b)` | Dtypes; diff two files |
| `data_quality(file, null_threshold?)` | Duplicates, nulls, constants, mixed types, padding |
| `check_data_contract(file, contract)` | Validate dtype/nullable/unique/min/max/allowed |
| `query_sql(sql, limit?)` | Read-only SELECT via `DATABASE_URL` |
| `convert_to_parquet(file, output_name?)` | [write] To Parquet in `outputs/` |
| `notebook_scan_secrets(notebook)` | Secret locations only, never values |
| `notebook_strip_outputs(notebook, output_name?)` | [write] Cleaned notebook copy |

### Resources and prompts
Resources (read-only context): `toolbox://files/inputs`, `toolbox://files/outputs`, `toolbox://pdf/{file}/info` (pages, encrypted, needs_ocr), `toolbox://guide`.
Prompts (templates): `summarize_pdf(file)`, `extract_section(file, topic)`, `clean_scan(file)`, `publish_notebook(notebook, tags)`, `profile_dataset(file)`, `find_data_quality_issues(file)`, `validate_contract(file, contract_json)`.
Also resources `toolbox://data/{file}/schema` and `toolbox://data/{file}/profile`.

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
