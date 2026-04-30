import my_toolbox.notion_tools as notion_tools


def test_init_requires_token_and_database(monkeypatch):
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)

    try:
        notion_tools.NotionTools()
        assert False, "Expected ValueError for missing token"
    except ValueError:
        pass


def test_build_sample_properties_uses_schema():
    out = notion_tools.NotionTools.build_sample_properties("title", "desc", "2024-01-01T00:00:00+00:00")
    assert "URL" in out
    assert "Title" in out
    assert "Published" in out


def test_create_get_update_delete(monkeypatch):
    calls = {"query_post": 0, "patch": 0}

    class Resp:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, headers=None, json=None, timeout=None):
        if "query" in url:
            calls["query_post"] += 1
        if "query" in url and calls["query_post"] == 1:
            return Resp({"results": [{"id": "1"}], "has_more": True, "next_cursor": "abc"})
        if "query" in url and calls["query_post"] == 2:
            return Resp({"results": [{"id": "2"}], "has_more": False, "next_cursor": None})
        return Resp({"id": "new-page"})

    def fake_patch(url, json=None, headers=None, timeout=None):
        calls["patch"] += 1
        return Resp({"ok": True, "url": url})

    monkeypatch.setattr(notion_tools.requests, "post", fake_post)
    monkeypatch.setattr(notion_tools.requests, "patch", fake_patch)

    nt = notion_tools.NotionTools(notion_token="t", database_id="d")

    created = nt.create_page({"k": "v"})
    assert created["id"] == "new-page"

    pages = nt.get_pages()
    assert len(pages) == 2

    updated = nt.update_page("pid", {"x": 1})
    assert updated["ok"] is True

    deleted = nt.delete_page("pid")
    assert deleted["ok"] is True
    assert calls["patch"] == 2
