import importlib
import sys
import types

import pytest


def _load_chat_module(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_DB_PATH", str(tmp_path / "chat_history.db"))
    monkeypatch.delenv("CHAT_DB_BACKEND", raising=False)
    sys.modules.pop("llm_toolbox.chat", None)
    import llm_toolbox.chat as chat

    return importlib.reload(chat)


def test_mode_helpers(monkeypatch, tmp_path):
    chat = _load_chat_module(monkeypatch, tmp_path)

    assert chat.normalize_mode("RAG") == "rag"
    assert chat.resolve_mode("auto", rag_enabled=True) == "rag"
    assert chat.resolve_mode("auto", rag_enabled=False) == "simple"

    with pytest.raises(ValueError):
        chat.normalize_mode("invalid")


def test_generate_assistant_reply_simple_uses_history_and_user_text(monkeypatch, tmp_path):
    chat = _load_chat_module(monkeypatch, tmp_path)
    captured = {}

    class DummyClient:
        def complete(self, messages):
            captured["messages"] = messages
            return "assistant reply"

    history = [chat.ChatMessage(role="system", content="Be brief")]
    mode_config = chat.ChatModeConfig(mode="simple")

    reply = chat.generate_assistant_reply(
        user_text="Hello",
        history=history,
        llm_client=DummyClient(),
        llm_provider="ollama",
        mode_config=mode_config,
    )

    assert reply == "assistant reply"
    assert [message.role for message in captured["messages"]] == ["system", "user"]
    assert captured["messages"][-1].content == "Hello"


def test_generate_assistant_reply_rag_delegates_to_query_rag(monkeypatch, tmp_path):
    chat = _load_chat_module(monkeypatch, tmp_path)
    fake_query_module = types.ModuleType("llm_toolbox.query_rag")
    captured = {}

    def fake_query_rag(query_text, **kwargs):
        captured["query_text"] = query_text
        captured["kwargs"] = kwargs
        return "rag reply"

    fake_query_module.query_rag = fake_query_rag
    monkeypatch.setitem(sys.modules, "llm_toolbox.query_rag", fake_query_module)

    reply = chat.generate_assistant_reply(
        user_text="What is in the docs?",
        history=[],
        llm_client=object(),
        llm_provider="gemini",
        mode_config=chat.ChatModeConfig(
            mode="rag",
            rag_embed_provider="ollama",
            rag_db_backend="chroma",
            rag_collection="documents",
            rag_top_k=3,
        ),
    )

    assert reply == "rag reply"
    assert captured["query_text"] == "What is in the docs?"
    assert captured["kwargs"] == {
        "embed_provider": "ollama",
        "db_backend": "chroma",
        "llm_provider": "gemini",
        "collection": "documents",
        "top_k": 3,
    }


def test_model_helpers(monkeypatch, tmp_path):
    _load_chat_module(monkeypatch, tmp_path)
    from llm_toolbox.clients import default_model_for_provider, infer_provider_from_model

    assert default_model_for_provider("ollama") == "llama3.2:1b"
    assert infer_provider_from_model("gemini-1.5-flash") == "gemini"
    assert infer_provider_from_model("moonshot-v1-8k") == "kimi"
    assert infer_provider_from_model("unknown-model") == "ollama"