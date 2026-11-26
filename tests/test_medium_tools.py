import base64
import json

import pytest

from my_toolbox.web import medium_tools as mt

PNG = base64.b64encode(b"fakepng").decode()

NOTEBOOK = {
    "metadata": {"language_info": {"name": "python"}},
    "cells": [
        {"cell_type": "markdown", "source": ["# My Post\n", "intro"]},
        {"cell_type": "code", "source": ["print(1)"], "metadata": {}, "outputs": [
            {"output_type": "stream", "name": "stdout", "text": ["1\n"]},
            {"output_type": "display_data", "data": {"image/png": PNG, "text/plain": "<Figure>"}},
        ]},
        {"cell_type": "code", "source": "secret()", "metadata": {"tags": ["remove-cell"]}, "outputs": []},
    ],
}


def test_notebook_to_markdown():
    md = mt.notebook_to_markdown(NOTEBOOK, image_uploader=lambda b, m: "http://img/1.png", title="My Post")
    assert not md.startswith("# My Post")
    assert "intro" in md and "```python\nprint(1)\n```" in md
    assert "![output](http://img/1.png)" in md
    assert "secret" not in md and "<Figure>" not in md

    plain = mt.notebook_to_markdown(NOTEBOOK, include_code=False)
    assert "print(1)" not in plain and "![" not in plain


class FakeResp:
    ok = True

    def __init__(self, data):
        self._data = data

    def json(self):
        return {"data": self._data}


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        if url.endswith("/me"):
            return FakeResp({"id": "u1"})
        if url.endswith("/images"):
            return FakeResp({"url": "http://img/up.png"})
        return FakeResp({"id": "p1", "url": "http://medium/p1"})


def test_publish_notebook_draft(tmp_path):
    nb = tmp_path / "n.ipynb"
    nb.write_text(json.dumps(NOTEBOOK))
    session = FakeSession()
    post = mt.MediumPublisher(token="t", session=session).publish_notebook(nb, tags=list("abcdefg"))

    assert post["id"] == "p1"
    method, url, kw = session.calls[-1]
    assert url.endswith("/users/u1/posts")
    assert kw["json"]["publishStatus"] == "draft" and len(kw["json"]["tags"]) == 5
    assert kw["json"]["content"].startswith("# My Post") and "http://img/up.png" in kw["json"]["content"]


def test_token_required(monkeypatch):
    monkeypatch.delenv("MEDIUM_TOKEN", raising=False)
    with pytest.raises(ValueError):
        mt.MediumPublisher()
