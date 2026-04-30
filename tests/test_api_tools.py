import my_toolbox.api_tools as api_tools


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def __contains__(self, key):
        return key in self._payload


def test_rapid_api_calls_success_with_headers_params(monkeypatch, dummy_logger):
    tool = api_tools.ApiTools(dummy_logger)

    def fake_get(url, headers=None, params=None, verify=None, timeout=None):
        assert url == "https://example.com"
        assert headers == {"k": "v"}
        assert params == {"q": "x"}
        assert verify is False
        assert timeout == 10
        return _Resp(200, {"data": {"ok": True}})

    monkeypatch.setattr(api_tools.time, "sleep", lambda *_: None)
    monkeypatch.setattr(api_tools.requests, "get", fake_get)

    out = tool.rapid_api_calls(
        {"url": "https://example.com", "headers": {"k": "v"}},
        dummy_logger,
        params={"q": "x"},
    )
    assert out == {"ok": True}


def test_rapid_api_calls_success_without_headers(monkeypatch, dummy_logger):
    tool = api_tools.ApiTools(dummy_logger)

    monkeypatch.setattr(api_tools.time, "sleep", lambda *_: None)
    monkeypatch.setattr(
        api_tools.requests,
        "get",
        lambda *args, **kwargs: _Resp(200, {"hello": "world"}),
    )

    out = tool.rapid_api_calls({"url": "https://example.com"}, dummy_logger)
    assert out == {"hello": "world"}


def test_handle_status_code_known_and_unknown(dummy_logger):
    tool = api_tools.ApiTools(dummy_logger)
    tool.handle_status_code(404)
    tool.handle_status_code(999)
    joined = " | ".join(str(m) for m in dummy_logger.messages)
    assert "Not Found" in joined
    assert "Unexpected status code" in joined
