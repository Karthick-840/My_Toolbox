import base64
import io

import pytest

pytest.importorskip("flask")

from PIL import Image
from reportlab.pdfgen import canvas

from app.pdf_app import create_app


def _pdf_bytes(text):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.save()
    return buf.getvalue()


@pytest.fixture
def client(tmp_path):
    return create_app(tmp_path).test_client()


def _upload(client, name, data):
    res = client.post("/api/upload", data={"files": (io.BytesIO(data), name)})
    assert res.status_code == 200


def test_index_and_listing(client):
    assert client.get("/").status_code == 200
    assert client.get("/api/files").get_json() == {"inputs": [], "outputs": []}


def test_text_merge_split_flow(client):
    _upload(client, "a.pdf", _pdf_bytes("alpha"))
    _upload(client, "b.pdf", _pdf_bytes("beta"))

    res = client.post("/api/op/text", json={"files": ["a.pdf"]})
    assert "alpha" in res.get_json()["text"]["a.pdf"]

    res = client.post("/api/op/merge", json={"files": ["a.pdf", "b.pdf"], "name": "both.pdf"})
    assert res.get_json()["new_outputs"] == ["both.pdf"]

    res = client.post("/api/op/split", json={"files": ["a.pdf"]})
    assert "a_page_1.pdf" in res.get_json()["new_outputs"]
    assert client.get("/files/outputs/both.pdf").status_code == 200


def test_write_text_and_snap_to_pdf(client):
    res = client.post("/api/op/write_text", json={"name": "../n.pdf", "content": "hi"})
    assert res.get_json()["new_outputs"] == ["n.pdf"]

    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    res = client.post("/api/op/images_to_pdf", json={"images": [url], "name": "snap"})
    assert res.get_json()["new_outputs"] == ["snap.pdf"]
    assert client.post("/api/op/images_to_pdf", json={"images": []}).status_code == 400


def test_errors(client):
    assert client.post("/api/op/text", json={"files": []}).status_code == 400
    assert client.post("/api/op/nope", json={}).status_code == 404
    assert client.get("/files/other/x").status_code == 404


def test_extract_pages_and_remove_blank_ops(client):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "one")
    c.showPage()
    c.showPage()
    c.drawString(100, 750, "three")
    c.save()
    _upload(client, "doc.pdf", buf.getvalue())

    res = client.post("/api/op/extract_pages", json={"files": ["doc.pdf"], "ranges": "1,3"})
    assert res.get_json()["new_outputs"] == ["doc_pages.pdf"]
    assert client.post("/api/op/extract_pages", json={"files": ["doc.pdf"], "ranges": "9"}).status_code == 400

    res = client.post("/api/op/remove_blank", json={"files": ["doc.pdf"]})
    assert "removed 1 blank" in res.get_json()["message"]
    assert "doc_noblank.pdf" in res.get_json()["new_outputs"]
