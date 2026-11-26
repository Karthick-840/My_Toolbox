import my_toolbox.notion_tools as notion_tools


def test_notion_master_requires_token(monkeypatch):
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    try:
        notion_tools.NotionMaster()
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_notion_master_build_simple_property():
    prop = notion_tools.NotionMaster.build_simple_property("Hello")
    assert "title" in prop
    assert prop["title"][0]["text"]["content"] == "Hello"


def test_notion_master_core_calls(monkeypatch):
    class Resp:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = "ok"

        def json(self):
            return self._payload

    def fake_post(url, json=None, headers=None, timeout=None):
        if url.endswith("/query"):
            return Resp({"results": [{"id": "1"}], "has_more": False, "next_cursor": None})
        if url.endswith("/search"):
            return Resp({"results": [{"id": "s1"}]})
        if url.endswith("/comments"):
            return Resp({"id": "c1"})
        return Resp({"id": "new"})

    def fake_patch(url, json=None, headers=None, timeout=None):
        return Resp({"ok": True, "url": url, "payload": json})

    def fake_get(url, headers=None, timeout=None):
        return Resp({"results": [{"id": "b1"}]})

    monkeypatch.setattr(notion_tools.requests, "post", fake_post)
    monkeypatch.setattr(notion_tools.requests, "patch", fake_patch)
    monkeypatch.setattr(notion_tools.requests, "get", fake_get)

    nm = notion_tools.NotionMaster(token="t", database_id="d")

    assert len(nm.query_database()) == 1
    assert nm.create_page({"Name": {"title": [{"text": {"content": "A"}}]}})["id"] == "new"
    assert nm.update_page("p1", {"k": "v"})["ok"] is True
    assert nm.delete_page("p1")["ok"] is True
    assert len(nm.get_block_children("p1")) == 1
    assert nm.append_content("p1", [{"object": "block"}])["ok"] is True
    assert nm.add_comment("p1", "hello")["id"] == "c1"
    assert len(nm.search("abc")) == 1


def test_notion_tools_unified_api(monkeypatch):
    class Resp:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = "ok"

        def json(self):
            return self._payload

    monkeypatch.setattr(notion_tools.requests, "post", lambda *a, **k: Resp({"id": "new"}))
    monkeypatch.setattr(notion_tools.requests, "patch", lambda *a, **k: Resp({"ok": True}))
    monkeypatch.setattr(notion_tools.requests, "get", lambda *a, **k: Resp({"ok": True}))

    nt = notion_tools.NotionTools(token="t", database_id="d")
    assert nt.modify_object("pages", properties={"Name": {}})["id"] == "new"
    assert nt.modify_object("pages", obj_id="p1", properties={"archived": True})["ok"] is True
    assert nt.manage_data_structure("search", title="abc")["id"] == "new"
    assert nt.interact("p1", text="hi")["id"] == "new"
