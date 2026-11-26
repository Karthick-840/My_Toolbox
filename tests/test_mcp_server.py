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
    server.set_limits(allow_write=True, max_rows=1000, max_bytes=50 * 1024 * 1024)
    yield tmp_path
    server.set_limits(allow_write=False)


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


def test_write_tools_blocked_by_default(ws):
    server.set_limits(allow_write=False)
    _pdf(ws / "inputs" / "a.pdf", "alpha")
    with pytest.raises(PermissionError):
        server.merge_pdfs(["a.pdf"], "x")
    with pytest.raises(PermissionError):
        server.convert_to_parquet("a.csv")
    assert "alpha" in server.extract_text("a.pdf")["text"]


def test_data_tools(ws):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    pd.DataFrame({"id": [1, 2, 2], "name": ["a", " b", " b"]}).to_csv(ws / "inputs" / "d.csv", index=False)
    pd.DataFrame({"id": [1], "extra": [1.5]}).to_csv(ws / "inputs" / "e.csv", index=False)
    prof = server.profile_data("d.csv")
    assert prof["rows"] == 3 and prof["duplicate_rows"] == 1
    assert server.data_schema("d.csv") == {"id": "int64", "name": "object"}
    cmp = server.compare_data_schemas("d.csv", "e.csv")
    assert cmp["only_in_a"] == ["name"] and cmp["only_in_b"] == ["extra"]
    kinds = {i["type"] for i in server.data_quality("d.csv")["issues"]}
    assert {"duplicate_rows", "whitespace_padding"} <= kinds
    ok = server.check_data_contract("d.csv", {"columns": {"id": {"unique": True}}})
    assert not ok["passed"]
    out = server.convert_to_parquet("d.csv")
    assert out["output"] == "outputs/d.parquet" and (ws / "outputs" / "d.parquet").is_file()


def test_query_sql_is_read_only_and_capped(ws, monkeypatch):
    pytest.importorskip("pandas")
    db = ws / "t.db"
    import sqlite3

    con = sqlite3.connect(db)
    con.execute("create table t(a int)")
    con.executemany("insert into t values (?)", [(i,) for i in range(10)])
    con.commit()
    con.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    res = server.query_sql("select a from t", limit=3)
    assert res["row_count"] == 3 and res["columns"] == ["a"]
    with pytest.raises(PermissionError):
        server.query_sql("delete from t")


def test_notebook_tools(ws):
    import json

    nb = {"cells": [{"cell_type": "code", "source": ["token = 'abcdefgh12345678'\n"],
                     "outputs": [{"output_type": "stream", "text": ["hi"]}],
                     "execution_count": 1, "metadata": {}}],
          "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    (ws / "inputs" / "n.ipynb").write_text(json.dumps(nb))
    assert not server.notebook_scan_secrets("n.ipynb")["clean"]
    res = server.notebook_strip_outputs("n.ipynb")
    assert res["outputs_cleared"] == 1
    assert json.loads((ws / "outputs" / "n.ipynb").read_text())["cells"][0]["outputs"] == []
