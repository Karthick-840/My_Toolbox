"""PDF Operations - local browser app exposing everything in my_toolbox.documents.pdf_tools.

Run from the repo root:  make app     (uv run --extra documents --group app python -m app.pdf_app)
Files live in ./workspace/inputs and ./workspace/outputs (override with PDF_APP_WORKSPACE).
"""

import base64
import binascii
import os
import re
import threading
import webbrowser
from io import BytesIO
from pathlib import Path

from my_toolbox.documents.pdf_tools import (
    PDF_Extract,
    PDF_FromImages,
    PDF_Manipulate,
    PDFAccess,
)

try:
    from flask import Flask, jsonify, render_template, request, send_from_directory
except ImportError:  # pragma: no cover
    Flask = None

HOST = "127.0.0.1"
PORT = 5050
DEFAULT_WORKSPACE = Path(os.environ.get("PDF_APP_WORKSPACE", Path.cwd() / "workspace"))


def _safe_name(name, default=None):
    cleaned = Path((name or "").strip()).name
    if not cleaned or cleaned in (".", ".."):
        if default:
            return default
        raise ValueError("A valid file name is required.")
    return cleaned


def create_app(workspace=DEFAULT_WORKSPACE):
    if Flask is None:
        raise ImportError("Flask is required. Run via: make app (uv run --group app ...)")

    workspace = Path(workspace).resolve()
    dirs = {"inputs": workspace / "inputs", "outputs": workspace / "outputs"}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    kw = {"input_path": str(dirs["inputs"]), "output_path": str(dirs["outputs"])}

    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024

    def listing(kind):
        return sorted(p.name for p in dirs[kind].iterdir() if p.is_file())

    def pdf_inputs(body):
        files = [_safe_name(f) for f in (body.get("files") or [])]
        if not files:
            raise ValueError("Select at least one input PDF.")
        missing = [f for f in files if not (dirs["inputs"] / f).is_file()]
        if missing:
            raise ValueError(f"Not found in inputs: {', '.join(missing)}")
        return files

    # Each operation takes the JSON body and returns a dict (message / text / tables).
    def op_text(body):
        ext, pattern = PDF_Extract(**kw), body.get("pattern")
        pattern = re.compile(pattern) if pattern else None
        page = int(body["page"]) if body.get("page") else None
        out = {}
        for f in pdf_inputs(body):
            if page or body.get("pagewise"):
                out[f] = ext.pagewise_text_extract(f, page_num=page)
                if pattern:
                    out[f] = {p: pattern.findall(t or "") for p, t in out[f].items()}
            else:
                out[f] = ext.complete_text_extract(f, pattern)
        return {"text": out}

    def op_images(body):
        ext, counts = PDF_Extract(**kw), {}
        for f in pdf_inputs(body):
            counts[f] = len(ext.extract_images(f))
        return {"message": "Extracted images: " + ", ".join(f"{k}: {v}" for k, v in counts.items())}

    def op_tables(body):
        ext, tables = PDF_Extract(**kw), {}
        for f in pdf_inputs(body):
            tables[f] = [t.to_html(index=False) for t in ext.extract_tables(f)]
        return {"tables": tables}

    def op_write_text(body):
        path = PDFAccess(**kw).write_text_to_pdf(
            _safe_name(body.get("name"), "text.pdf"),
            body.get("content") or "",
            int(body.get("x") or 100),
            int(body.get("y") or 750),
        )
        return {"message": f"Wrote {Path(path).name}"}

    def op_merge(body):
        files = pdf_inputs(body)
        name = Path(_safe_name(body.get("name"), "merged.pdf")).stem
        path = PDF_Manipulate(**kw).merge_pdfs(merge_dict=files, output_file_name=name)
        return {"message": f"Merged {len(files)} files into {Path(path).name}"}

    def op_split(body):
        man, total = PDF_Manipulate(**kw), 0
        for f in pdf_inputs(body):
            total += len(man.split_pdf_pages(f))
        return {"message": f"Split into {total} single-page PDFs"}

    def op_extract_pages(body):
        man, made = PDF_Manipulate(**kw), []
        files = pdf_inputs(body)
        for f in files:
            made.append(Path(man.extract_pages(f, body.get("ranges"))).name)
        return {"message": f"Created: {', '.join(made)}"}

    def op_remove_blank(body):
        man, notes = PDF_Manipulate(**kw), []
        for f in pdf_inputs(body):
            path, removed = man.remove_blank_pages(f, check_images=not body.get("text_only"))
            if path is None:
                notes.append(f"{f}: every page is blank, nothing written")
            else:
                notes.append(f"{f}: removed {len(removed)} blank page(s) {removed or ''}".strip())
        return {"message": "; ".join(notes)}

    def op_empty(body):
        moved = PDF_Manipulate(**kw).move_empty_pdfs(
            empty_folder=str(dirs["outputs"] / "empty"), delete=bool(body.get("delete"))
        )
        verb = "Deleted" if body.get("delete") else "Moved to outputs/empty"
        return {"message": f"{verb}: {', '.join(moved) if moved else 'no empty PDFs found'}"}

    def op_rename(body):
        renamed = PDF_Manipulate(**kw).sort_and_rename_files(rename=True)
        return {"message": f"Renamed {len(renamed)} files with 0001_ style prefixes"}

    def op_combine(body):
        try:
            order = [int(x) for x in re.split(r"[,\s]+", (body.get("order") or "").strip()) if x]
        except ValueError:
            raise ValueError("Order must be numbers like 1,3,2 (the 0001_ prefixes).")
        if not order:
            raise ValueError("Enter the prefix order, e.g. 1,3,2.")
        name = Path(_safe_name(body.get("name"), "combined.pdf")).stem
        written = PDF_Manipulate(**kw).combine_pdfs(name, {name: order})
        return {"message": f"Combined into {', '.join(Path(w).name for w in written)}"}

    def op_images_to_pdf(body):
        data_urls = body.get("images") or []
        if not data_urls:
            raise ValueError("No images to convert.")
        buffers = [BytesIO(base64.b64decode(u.split(",", 1)[-1])) for u in data_urls]
        name = _safe_name(body.get("name"), "untitled.pdf")
        path = PDF_FromImages(**kw).images_to_pdf(buffers, name)
        return {"message": f"Saved {Path(path).name}"}

    ops = {
        "text": op_text,
        "images": op_images,
        "tables": op_tables,
        "write_text": op_write_text,
        "merge": op_merge,
        "split": op_split,
        "extract_pages": op_extract_pages,
        "remove_blank": op_remove_blank,
        "empty": op_empty,
        "rename": op_rename,
        "combine": op_combine,
        "images_to_pdf": op_images_to_pdf,
    }

    @app.get("/")
    def index():
        return render_template("pdf_operations.html")

    @app.get("/api/files")
    def files():
        return jsonify(inputs=listing("inputs"), outputs=listing("outputs"))

    @app.post("/api/upload")
    def upload():
        saved = []
        for f in request.files.getlist("files"):
            name = _safe_name(f.filename)
            f.save(dirs["inputs"] / name)
            saved.append(name)
        return jsonify(saved=saved)

    @app.get("/files/<kind>/<path:name>")
    def download(kind, name):
        if kind not in dirs:
            return jsonify(error="Unknown folder."), 404
        return send_from_directory(dirs[kind], name, as_attachment=True)

    @app.delete("/files/<kind>/<path:name>")
    def delete(kind, name):
        if kind not in dirs:
            return jsonify(error="Unknown folder."), 404
        target = dirs[kind] / _safe_name(name)
        if not target.is_file():
            return jsonify(error="File not found."), 404
        target.unlink()
        return jsonify(deleted=target.name)

    @app.post("/api/op/<op>")
    def run_op(op):
        if op not in ops:
            return jsonify(error=f"Unknown operation: {op}"), 404
        before = set(listing("outputs"))
        try:
            result = ops[op](request.get_json(silent=True) or {})
        except (ValueError, binascii.Error, OSError, ImportError, re.error) as exc:
            return jsonify(error=str(exc)), 400
        except Exception as exc:  # surfaced in the UI; e.g. tabula needs Java
            return jsonify(error=f"{type(exc).__name__}: {exc}"), 500
        result["new_outputs"] = [n for n in listing("outputs") if n not in before]
        return jsonify(result)

    return app


def main():
    threading.Timer(0.8, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    create_app().run(host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    main()
