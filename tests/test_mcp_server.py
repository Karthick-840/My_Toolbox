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


def test_resources_and_prompts(ws):
    import asyncio

    _pdf(ws / "inputs" / "a.pdf", "alpha")
    prompts = {p.name for p in asyncio.run(server.mcp.list_prompts())}
    assert {"summarize_pdf", "clean_scan", "publish_notebook", "extract_section"} <= prompts
    uris = {str(r.uri) for r in asyncio.run(server.mcp.list_resources())}
    assert {"toolbox://files/inputs", "toolbox://guide"} <= uris
    templates = {t.uriTemplate for t in asyncio.run(server.mcp.list_resource_templates())}
    assert "toolbox://pdf/{file}/info" in templates
    info = server.pdf_info("a.pdf")
    assert info["pages"] == 1 and info["encrypted"] is False
    assert server.inputs_resource() == ["a.pdf"]
