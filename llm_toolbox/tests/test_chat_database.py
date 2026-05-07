from llm_toolbox.database_clients import SQLiteChatStore, get_chat_store


def test_sqlite_store_round_trip(tmp_path):
    db_path = tmp_path / "nested" / "chat_history.db"

    store = get_chat_store(backend="sqlite", sqlite_path=str(db_path))
    conversation = store.create_conversation(
        title="Test Session",
        mode="simple",
        provider="ollama",
        model="llama3.2:latest",
        metadata={"interface": "test"},
    )
    message = store.add_message(
        conversation_id=conversation.id,
        role="user",
        content="Hello",
        metadata={"turn": 1},
    )

    conversations = store.list_conversations()
    messages = store.get_messages(conversation.id)

    assert db_path.exists()
    assert conversation.metadata == {"interface": "test"}
    assert conversations[0].id == conversation.id
    assert messages[0].id == message.id
    assert messages[0].content == "Hello"
    assert messages[0].metadata == {"turn": 1}


def test_get_chat_store_defaults_to_sqlite(monkeypatch, tmp_path):
    db_path = tmp_path / "default_chat.db"
    monkeypatch.setenv("CHAT_DB_PATH", str(db_path))
    monkeypatch.delenv("CHAT_DB_BACKEND", raising=False)

    store = get_chat_store()

    assert isinstance(store, SQLiteChatStore)
    assert db_path.exists()


def test_get_chat_store_requires_postgres_dsn(monkeypatch):
    monkeypatch.delenv("CHAT_DB_DSN", raising=False)

    with __import__("pytest").raises(ValueError, match="CHAT_DB_DSN is required"):
        get_chat_store(backend="postgres")