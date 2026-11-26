import io

import pytest

pytest.importorskip("mcp")

from reportlab.pdfgen import canvas

from my_toolbox.mcp import server


def _pdf(path, text):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.save()
    path.write_bytes(buf.getvalue())


@pytest.fixture
def ws(tmp_path):
    server.set_workspace(tmp_path)
    return tmp_path


def test_merge_extract_split(ws):
    _pdf(ws / "inputs" / "a.pdf", "alpha")
    _pdf(ws / "inputs" / "b.pdf", "beta")
    assert server.list_files()["inputs"] == ["a.pdf", "b.pdf"]
    assert server.merge_pdfs(["a.pdf", "b.pdf"], "both") == "outputs/both.pdf"
    assert (ws / "outputs" / "both.pdf").is_file()
    assert "alpha" in server.extract_text("a.pdf")["text"]
    assert len(server.split_pdf("a.pdf")) == 1


@pytest.mark.parametrize("bad", ["../x.pdf", "sub/x.pdf", "/etc/passwd", ""])
def test_rejects_paths_outside_inputs(ws, bad):
    with pytest.raises(ValueError):
        server.extract_text(bad)


def test_missing_file(ws):
    with pytest.raises(FileNotFoundError):
        server.extract_text("nope.pdf")


def test_tools_registered():
    import asyncio

    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"merge_pdfs", "extract_pages", "notebook_to_medium"} <= names
