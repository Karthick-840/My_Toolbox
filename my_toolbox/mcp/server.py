"""MCP server for my_toolbox (stdio by default).

All file access is confined to one workspace (env MY_TOOLBOX_WORKSPACE, default ./workspace)
with `inputs/` for sources and `outputs/` for results. Tool arguments are bare file names.

Run:  my-toolbox-mcp            (stdio)
      my-toolbox-mcp --workspace /data/work
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

from my_toolbox.documents.pdf_tools import (
    PDF_Extract,
    PDF_FromImages,
    PDF_Manipulate,
    PDFAccess,
)

mcp = FastMCP("my-toolbox")

_workspace = Path(os.environ.get("MY_TOOLBOX_WORKSPACE", "workspace"))


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
    """Extract text from a PDF in inputs/. Optional 1-based page and a regex to return matches only."""
    name = _existing(file)
    ext = PDF_Extract(**_kw())
    rx = re.compile(pattern) if pattern else None
    if page:
        pages = ext.pagewise_text_extract(name, page_num=page)
        return {"pages": {p: (rx.findall(t or "") if rx else t) for p, t in pages.items()}}
    return {"text": ext.complete_text_extract(name, rx)}


@mcp.tool()
def extract_pages(file: str, ranges: str, output_name: str | None = None) -> str:
    """Create a new PDF from page ranges such as '3-7,10,12-'. Returns the output path."""
    name = _existing(file)
    out = _name(output_name) if output_name else None
    return _out(PDF_Manipulate(**_kw()).extract_pages(name, ranges, out))


@mcp.tool()
def merge_pdfs(files: list[str], output_name: str = "merged") -> str:
    """Merge PDFs from inputs/ in the given order. Returns the output path."""
    names = [_existing(f) for f in files]
    if not names:
        raise ValueError("Provide at least one file.")
    stem = Path(_name(output_name)).stem
    return _out(PDF_Manipulate(**_kw()).merge_pdfs(merge_dict=names, output_file_name=stem))


@mcp.tool()
def split_pdf(file: str) -> list[str]:
    """Split a PDF into single-page PDFs in outputs/. Returns the output paths."""
    name = _existing(file)
    return [_out(p) for p in PDF_Manipulate(**_kw()).split_pdf_pages(name)]


@mcp.tool()
def remove_blank_pages(file: str, text_only: bool = False) -> dict:
    """Remove blank pages (pages with no text and, unless text_only, no images)."""
    name = _existing(file)
    path, removed = PDF_Manipulate(**_kw()).remove_blank_pages(name, check_images=not text_only)
    return {"output": _out(path) if path else None, "removed_pages": removed}


@mcp.tool()
def images_to_pdf(images: list[str], output_name: str = "images.pdf") -> str:
    """Combine image files from inputs/ (in order) into one PDF. Returns the output path."""
    inputs = _dirs()[0]
    paths = [str(inputs / _existing(i)) for i in images]
    return _out(PDF_FromImages(**_kw()).images_to_pdf(paths, _name(output_name)))


@mcp.tool()
def write_text_pdf(output_name: str, content: str) -> str:
    """Write plain text into a new PDF. Returns the output path."""
    return _out(PDFAccess(**_kw()).write_text_to_pdf(_name(output_name), content))


@mcp.tool()
def notebook_to_medium(notebook: str, title: str | None = None, tags: list[str] | None = None,
                       status: str = "draft") -> dict:
    """Post a .ipynb from inputs/ to Medium (draft by default). Needs env MEDIUM_TOKEN."""
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="my_toolbox MCP server")
    parser.add_argument("--workspace", help="Workspace folder (default: ./workspace)")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    args = parser.parse_args(argv)
    if args.workspace:
        set_workspace(args.workspace)
    # stdout carries the stdio protocol; library print() calls must not pollute it
    sys.stdout = sys.stderr
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
