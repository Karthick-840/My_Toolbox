"""MCP server for my_toolbox (stdio by default).

All file access is confined to one workspace (env MY_TOOLBOX_WORKSPACE, default ./workspace)
with `inputs/` for sources and `outputs/` for results. Tool arguments are bare file names.

Safety: read-only by default. Tools that write files or call external services need
--allow-write (or MY_TOOLBOX_ALLOW_WRITE=1). Responses are capped by MY_TOOLBOX_MAX_ROWS
(default 1000), and inputs larger than MY_TOOLBOX_MAX_BYTES (default 50 MB) are refused.
SQL goes through DATABASE_URL and only accepts a single SELECT/WITH statement.

Run:  my-toolbox-mcp            (stdio, read-only)
      my-toolbox-mcp --workspace /data/work --allow-write
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise ImportError('Install the MCP extra: pip install "my-toolbox[mcp]"') from exc

from my_toolbox.data import quality
from my_toolbox.devops import notebook_tools
from my_toolbox.documents.pdf_tools import (
    PDF_Extract,
    PDF_FromImages,
    PDF_Manipulate,
    PDFAccess,
)

mcp = FastMCP("my-toolbox")

_workspace = Path(os.environ.get("MY_TOOLBOX_WORKSPACE", "workspace"))
_allow_write = os.environ.get("MY_TOOLBOX_ALLOW_WRITE", "").lower() in ("1", "true", "yes")
_max_rows = int(os.environ.get("MY_TOOLBOX_MAX_ROWS", "1000"))
_max_bytes = int(os.environ.get("MY_TOOLBOX_MAX_BYTES", str(50 * 1024 * 1024)))


def set_limits(allow_write=None, max_rows=None, max_bytes=None):
    global _allow_write, _max_rows, _max_bytes
    if allow_write is not None:
        _allow_write = allow_write
    if max_rows is not None:
        _max_rows = max_rows
    if max_bytes is not None:
        _max_bytes = max_bytes


def _require_write():
    if not _allow_write:
        raise PermissionError(
            "This tool writes files or calls external services. "
            "Start the server with --allow-write (or MY_TOOLBOX_ALLOW_WRITE=1) to enable it."
        )


def _data_file(value: str) -> Path:
    name = _existing(value)
    path = _dirs()[0] / name
    if path.stat().st_size > _max_bytes:
        raise ValueError(f"{name} is larger than the {_max_bytes} byte limit.")
    return path


def _clip(text: str) -> dict:
    if len(text) > _max_bytes:
        return {"text": text[:_max_bytes], "truncated": True}
    return {"text": text, "truncated": False}


def set_workspace(path) -> Path:
    global _workspace
    _workspace = Path(path)
    return _dirs()[0].parent


def _dirs():
    root = _workspace.resolve()
    inputs, outputs = root / "inputs", root / "outputs"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    return inputs, outputs


def _kw():
    inputs, outputs = _dirs()
    return {"input_path": str(inputs), "output_path": str(outputs)}


def _name(value: str) -> str:
    """Accept only a bare file name so tools cannot escape the workspace."""
    cleaned = Path((value or "").strip()).name
    if not cleaned or cleaned in (".", "..") or cleaned != value.strip():
        raise ValueError(f"Use a plain file name inside inputs/, got: {value!r}")
    return cleaned


def _existing(value: str) -> str:
    name = _name(value)
    if not (_dirs()[0] / name).is_file():
        raise FileNotFoundError(f"Not found in inputs: {name}")
    return name


def _out(path) -> str:
    return f"outputs/{Path(path).name}"


@mcp.tool()
def list_files() -> dict:
    """List files in the workspace inputs/ and outputs/ folders."""
    inputs, outputs = _dirs()
    return {
        "inputs": sorted(p.name for p in inputs.iterdir() if p.is_file()),
        "outputs": sorted(p.name for p in outputs.iterdir() if p.is_file()),
    }


@mcp.tool()
def extract_text(file: str, page: int | None = None, pattern: str | None = None) -> dict:
    """Extract text from a PDF in inputs/ (read-only; output capped). Optional 1-based page and regex."""
    name = _existing(file)
    ext = PDF_Extract(**_kw())
    rx = re.compile(pattern) if pattern else None
    if page:
        pages = ext.pagewise_text_extract(name, page_num=page)
        return {"pages": {p: (rx.findall(t or "") if rx else (t or "")[:_max_bytes])
                          for p, t in pages.items()}}
    result = ext.complete_text_extract(name, rx)
    return _clip(result) if isinstance(result, str) else {"matches": result[:_max_rows]}


@mcp.tool()
def extract_pages(file: str, ranges: str, output_name: str | None = None) -> str:
    """[write] Create a new PDF from page ranges such as '3-7,10,12-'. Returns the output path."""
    _require_write()
    name = _existing(file)
    out = _name(output_name) if output_name else None
    return _out(PDF_Manipulate(**_kw()).extract_pages(name, ranges, out))


@mcp.tool()
def merge_pdfs(files: list[str], output_name: str = "merged") -> str:
    """[write] Merge PDFs from inputs/ in the given order. Returns the output path."""
    _require_write()
    names = [_existing(f) for f in files]
    if not names:
        raise ValueError("Provide at least one file.")
    stem = Path(_name(output_name)).stem
    return _out(PDF_Manipulate(**_kw()).merge_pdfs(merge_dict=names, output_file_name=stem))


@mcp.tool()
def split_pdf(file: str) -> list[str]:
    """[write] Split a PDF into single-page PDFs in outputs/. Returns the output paths."""
    _require_write()
    name = _existing(file)
    return [_out(p) for p in PDF_Manipulate(**_kw()).split_pdf_pages(name)]


@mcp.tool()
def remove_blank_pages(file: str, text_only: bool = False) -> dict:
    """[write] Remove blank pages (pages with no text and, unless text_only, no images)."""
    _require_write()
    name = _existing(file)
    path, removed = PDF_Manipulate(**_kw()).remove_blank_pages(name, check_images=not text_only)
    return {"output": _out(path) if path else None, "removed_pages": removed}


@mcp.tool()
def images_to_pdf(images: list[str], output_name: str = "images.pdf") -> str:
    """[write] Combine image files from inputs/ (in order) into one PDF. Returns the output path."""
    _require_write()
    inputs = _dirs()[0]
    paths = [str(inputs / _existing(i)) for i in images]
    return _out(PDF_FromImages(**_kw()).images_to_pdf(paths, _name(output_name)))


@mcp.tool()
def write_text_pdf(output_name: str, content: str) -> str:
    """[write] Write plain text into a new PDF. Returns the output path."""
    _require_write()
    return _out(PDFAccess(**_kw()).write_text_to_pdf(_name(output_name), content))


@mcp.tool()
def notebook_to_medium(notebook: str, title: str | None = None, tags: list[str] | None = None,
                       status: str = "draft") -> dict:
    """[write] Post a .ipynb from inputs/ to Medium (draft by default). Needs env MEDIUM_TOKEN."""
    _require_write()
    from my_toolbox.web.medium_tools import MediumPublisher

    name = _existing(notebook)
    result = MediumPublisher().publish_notebook(
        _dirs()[0] / name, title=title, tags=tags, status=status
    )
    return {"id": result.get("id"), "url": result.get("url"), "status": result.get("publishStatus")}


@mcp.resource("toolbox://files/inputs", mime_type="application/json")
def inputs_resource() -> list[str]:
    """File names currently in the workspace inputs/ folder."""
    return list_files()["inputs"]


@mcp.resource("toolbox://files/outputs", mime_type="application/json")
def outputs_resource() -> list[str]:
    """File names currently in the workspace outputs/ folder."""
    return list_files()["outputs"]


@mcp.resource("toolbox://pdf/{file}/info", mime_type="application/json")
def pdf_info(file: str) -> dict:
    """Page count, encryption flag and whether the PDF looks scanned (needs OCR)."""
    name = _existing(file)
    access = PDFAccess(**_kw())
    reader = access.read_pdf(name)
    info = {"file": name, "pages": len(reader.pages), "encrypted": bool(reader.is_encrypted)}
    try:
        info["needs_ocr"] = access.needs_ocr(name)
    except Exception:  # PyMuPDF missing or unreadable file
        info["needs_ocr"] = None
    return info


@mcp.resource("toolbox://guide", mime_type="text/markdown")
def guide() -> str:
    """How the workspace and tools work."""
    return (
        "Files live in the workspace: put sources in `inputs/`, results appear in `outputs/`.\n"
        "Pass bare file names (no paths). Page ranges look like `3-7,10,12-`.\n"
        "Read `toolbox://files/inputs` to see available files and "
        "`toolbox://pdf/{file}/info` to inspect a PDF before acting."
    )


@mcp.prompt()
def summarize_pdf(file: str) -> str:
    """Summarise a PDF from inputs/."""
    return (
        f"Read toolbox://pdf/{file}/info. If needs_ocr is true, say the file is a scan and stop. "
        f"Otherwise call extract_text for '{file}' and write a concise summary with key points."
    )


@mcp.prompt()
def extract_section(file: str, topic: str) -> str:
    """Find the pages about a topic and save them as a new PDF."""
    return (
        f"Call extract_text for '{file}' page by page, find the pages about '{topic}', "
        "then call extract_pages with those page ranges and report the output file."
    )


@mcp.prompt()
def clean_scan(file: str) -> str:
    """Remove blank pages from a scanned PDF."""
    return (
        f"Call remove_blank_pages for '{file}'. Report which pages were removed and the output "
        "file. If nothing was removed, say so."
    )


@mcp.prompt()
def publish_notebook(notebook: str, tags: str = "") -> str:
    """Publish a notebook to Medium as a draft."""
    return (
        f"Call notebook_to_medium for '{notebook}' with tags [{tags}] and status 'draft'. "
        "Return the draft URL. Never publish publicly unless the user asks."
    )


@mcp.tool()
def profile_data(file: str, sample_rows: int = 5) -> dict:
    """Profile a CSV/TSV/Parquet/JSON/Excel file in inputs/: counts, nulls, distinct, stats, sample."""
    df = quality.read_table(_data_file(file))
    return quality.profile(df, sample_rows=min(sample_rows, _max_rows))


@mcp.tool()
def data_schema(file: str) -> dict:
    """Column names and dtypes of a data file in inputs/."""
    return quality.schema(quality.read_table(_data_file(file), nrows=_max_rows))


@mcp.tool()
def compare_data_schemas(file_a: str, file_b: str) -> dict:
    """Compare columns and dtypes of two data files in inputs/."""
    a = quality.read_table(_data_file(file_a), nrows=_max_rows)
    b = quality.read_table(_data_file(file_b), nrows=_max_rows)
    return quality.compare_schemas(a, b)


@mcp.tool()
def data_quality(file: str, null_threshold: float = 50.0) -> dict:
    """Heuristic data-quality issues: duplicates, nulls, constants, mixed types, padded text."""
    df = quality.read_table(_data_file(file))
    issues = quality.quality_issues(df, null_threshold)
    return {"rows": len(df), "issue_count": len(issues), "issues": issues[:_max_rows]}


@mcp.tool()
def check_data_contract(file: str, contract: dict) -> dict:
    """Validate a data file against a contract (columns -> dtype/nullable/unique/min/max/allowed)."""
    df = quality.read_table(_data_file(file))
    problems = quality.check_contract(df, contract)
    return {"passed": not problems, "violations": problems[:_max_rows]}


@mcp.tool()
def query_sql(sql: str, limit: int = 100) -> dict:
    """Run a read-only SELECT/WITH against the database in env DATABASE_URL (rows capped)."""
    from my_toolbox.data.sql_tools import SQLClient

    cap = max(1, min(limit, _max_rows))
    with SQLClient(read_only=True) as client:
        df = client.query(sql, max_rows=cap)
    return {"columns": list(df.columns), "rows": df.astype(object).where(df.notna(), None).values.tolist(),
            "row_count": len(df), "capped_at": cap}


@mcp.tool()
def convert_to_parquet(file: str, output_name: str | None = None) -> dict:
    """[write] Convert a data file in inputs/ to Parquet in outputs/."""
    _require_write()
    src = _data_file(file)
    out = _name(output_name) if output_name else src.stem + ".parquet"
    result = quality.to_parquet(src, _dirs()[1] / out)
    result["output"] = _out(out)
    return result


@mcp.tool()
def notebook_scan_secrets(notebook: str) -> dict:
    """Scan a notebook in inputs/ for likely secrets (locations only, never the values)."""
    findings = notebook_tools.find_secrets(_data_file(notebook))
    return {"clean": not findings, "findings": findings[:_max_rows]}


@mcp.tool()
def notebook_strip_outputs(notebook: str, output_name: str | None = None) -> dict:
    """[write] Write a copy of a notebook with outputs and execution counts cleared to outputs/."""
    _require_write()
    src = _data_file(notebook)
    out = _name(output_name) if output_name else src.name
    result = notebook_tools.strip_outputs(src, _dirs()[1] / out)
    result["output"] = _out(out)
    return result


@mcp.resource("toolbox://data/{file}/schema", mime_type="application/json")
def data_schema_resource(file: str) -> dict:
    """Schema of a data file in inputs/."""
    return data_schema(file)


@mcp.resource("toolbox://data/{file}/profile", mime_type="application/json")
def data_profile_resource(file: str) -> dict:
    """Profile of a data file in inputs/."""
    return profile_data(file)


@mcp.prompt()
def profile_dataset(file: str) -> str:
    """Profile a dataset and summarise its shape and risks."""
    return (
        f"Call profile_data for '{file}'. Summarise rows, columns, null-heavy columns and "
        "duplicates, then list the three most important things to fix before analysis."
    )


@mcp.prompt()
def find_data_quality_issues(file: str) -> str:
    """Audit a dataset and propose fixes."""
    return (
        f"Call data_quality for '{file}', then data_schema. Group the issues by severity and "
        "propose a concrete fix for each. Do not modify the data."
    )


@mcp.prompt()
def validate_contract(file: str, contract_json: str) -> str:
    """Validate a dataset against a JSON contract."""
    return (
        f"Parse this contract: {contract_json}. Call check_data_contract for '{file}' with it and "
        "report pass/fail with each violation."
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="my_toolbox MCP server")
    parser.add_argument("--workspace", help="Workspace folder (default: ./workspace)")
    parser.add_argument("--allow-write", action="store_true",
                        help="Enable tools that write files or call external services")
    parser.add_argument("--max-rows", type=int, help="Cap on rows/items returned (default 1000)")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    args = parser.parse_args(argv)
    if args.workspace:
        set_workspace(args.workspace)
    set_limits(allow_write=True if args.allow_write else None, max_rows=args.max_rows)
    # stdout carries the stdio protocol; library print() calls must not pollute it
    sys.stdout = sys.stderr
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
