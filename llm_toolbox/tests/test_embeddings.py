import importlib
import json
import sys
import types


def _load_embeddings_module(monkeypatch):
    fake_pydantic = types.ModuleType("pydantic")

    class _BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self, exclude_none=False):
            data = self.__dict__.copy()
            if exclude_none:
                data = {k: v for k, v in data.items() if v is not None}
            return data

    def _field(default=None, **_kwargs):
        return default

    fake_pydantic.BaseModel = _BaseModel
    fake_pydantic.Field = _field
    monkeypatch.setitem(sys.modules, "pydantic", fake_pydantic)

    sys.modules.pop("llm_toolbox.models", None)
    sys.modules.pop("llm_toolbox.embeddings", None)
    import llm_toolbox.embeddings as embeddings

    return importlib.reload(embeddings)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_openai_embedder_posts_to_embeddings_endpoint(monkeypatch):
    embeddings = _load_embeddings_module(monkeypatch)
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
            ]
        })

    monkeypatch.setattr(embeddings.urllib.request, "urlopen", fake_urlopen)

    embedder = embeddings.get_embedder(
        "openai",
        api_key="openai-token",
        model="text-embedding-3-small",
    )
    vector = embedder.embed_query("hello world")

    assert vector == [0.1, 0.2, 0.3]
    assert captured["url"] == "https://api.openai.com/v1/embeddings"
    assert captured["payload"] == {
        "model": "text-embedding-3-small",
        "input": ["hello world"],
    }
    assert captured["headers"]["Authorization"] == "Bearer openai-token"


def test_deepseek_embedder_uses_openai_compatible_shape(monkeypatch):
    embeddings = _load_embeddings_module(monkeypatch)
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({
            "data": [
                {"index": 0, "embedding": [1.0, 2.0]},
                {"index": 1, "embedding": [3.0, 4.0]},
            ]
        })

    monkeypatch.setattr(embeddings.urllib.request, "urlopen", fake_urlopen)

    doc_one = embeddings.Document(content="first")
    doc_two = embeddings.Document(content="second")
    embedder = embeddings.get_embedder("deepseek", api_key="deepseek-token")
    vectors = embedder.embed_documents([doc_one, doc_two])

    assert vectors == [[1.0, 2.0], [3.0, 4.0]]
    assert captured["url"] == "https://api.deepseek.com/v1/embeddings"
    assert captured["payload"]["model"] == "deepseek-embedding"
    assert captured["payload"]["input"] == ["first", "second"]


def test_kimi_embedder_reads_api_key_from_env(monkeypatch):
    embeddings = _load_embeddings_module(monkeypatch)
    monkeypatch.setenv("KIMI_API_KEY", "kimi-token")

    embedder = embeddings.get_embedder("kimi", model="moonshot-embedding-v1")

    assert embedder.api_key == "kimi-token"
    assert embedder.base_url == "https://api.moonshot.cn/v1"
    assert embedder.model == "moonshot-embedding-v1"


def test_get_embedder_rejects_unknown_provider(monkeypatch):
    embeddings = _load_embeddings_module(monkeypatch)

    try:
        embeddings.get_embedder("unknown-provider")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown provider")

    assert "openai" in message
    assert "deepseek" in message
    assert "kimi" in message
