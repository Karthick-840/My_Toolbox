"""Notebook hygiene and headless runs: strip outputs, scan for secrets, run with parameters.

strip_outputs and find_secrets use only the standard library; run_notebook needs the
`notebooks` extra (nbformat, nbclient, ipykernel).
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "generic_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"
    ),
}


def _load(path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _src(cell) -> str:
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def strip_outputs(path, output_path: Optional[str] = None, keep_metadata: bool = False) -> Dict[str, int]:
    """Clear outputs and execution counts (in place unless output_path is given)."""
    nb = _load(path)
    cleared = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            cleared += len(cell.get("outputs", []))
            cell["outputs"] = []
            cell["execution_count"] = None
        if not keep_metadata:
            cell.get("metadata", {}).pop("execution", None)
    Path(output_path or path).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    return {"cells": len(nb.get("cells", [])), "outputs_cleared": cleared}


def find_secrets(path) -> List[Dict[str, Any]]:
    """Scan code, markdown and outputs for likely secrets; values are never returned."""
    nb = _load(path)
    findings = []
    for i, cell in enumerate(nb.get("cells", [])):
        texts = [("source", _src(cell))]
        for out in cell.get("outputs", []):
            body = out.get("text") or out.get("data", {}).get("text/plain") or ""
            texts.append(("output", "".join(body) if isinstance(body, list) else body))
        for where, text in texts:
            for kind, rx in SECRET_PATTERNS.items():
                for match in rx.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    findings.append({"cell": i, "where": where, "type": kind, "line": line})
    return findings


def run_notebook(path, output_path, parameters: Optional[Dict[str, Any]] = None,
                 timeout: int = 600, kernel: str = "python3") -> Dict[str, Any]:
    """Execute a notebook headless. Parameters are injected as a cell after the one tagged
    'parameters' (or at the top if none), papermill style."""
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as exc:
        raise ImportError('Install notebooks extra: pip install "my-toolbox[notebooks]"') from exc

    nb = nbformat.read(str(path), as_version=4)
    if parameters:
        code = "\n".join(f"{k} = {v!r}" for k, v in parameters.items())
        cell = nbformat.v4.new_code_cell(code)
        cell.metadata["tags"] = ["injected-parameters"]
        idx = next((i + 1 for i, c in enumerate(nb.cells)
                    if "parameters" in c.get("metadata", {}).get("tags", [])), 0)
        nb.cells.insert(idx, cell)
    NotebookClient(nb, timeout=timeout, kernel_name=kernel, resources={"metadata": {"path": str(Path(path).parent)}}).execute()
    nbformat.write(nb, str(output_path))
    return {"output": str(output_path), "cells": len(nb.cells)}
