"""Web/API server for OpenAI/OpenWebUI-compatible chat endpoints."""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

from llm_toolbox.database_clients import get_chat_store
from llm_toolbox.chat import ChatModeConfig, generate_assistant_reply, resolve_mode
from llm_toolbox.clients import ChatMessage, get_llm_client, infer_provider_from_model

CHAT_STORE = get_chat_store(
    backend=os.getenv("CHAT_DB_BACKEND", "sqlite"),
    sqlite_path=os.getenv("CHAT_DB_PATH", "llm_toolbox/db/chat_database.db"),
    postgres_dsn=os.getenv("CHAT_DB_DSN"),
)

app = None


def ensure_web_app():
    global app
    if app is not None:
        return app

    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise ImportError(
            "fastapi and pydantic are required for web chat server features. "
            "Install with: pip install fastapi pydantic uvicorn"
        ) from exc

    class ChatCompletionMessage(BaseModel):
        role: str
        content: str

    class ChatCompletionRequest(BaseModel):
        model: str = Field(default="llama3.2:latest")
        messages: List[ChatCompletionMessage]
        temperature: float = 0.2
        stream: bool = False
        provider: Optional[str] = None
        mode: str = Field(default="simple")
        conversation_id: Optional[str] = None
        rag_embed_provider: Optional[str] = None
        rag_db_backend: str = "chroma"
        rag_collection: str = "documents"
        rag_top_k: int = 5

    class ConversationCreateRequest(BaseModel):
        title: str = "API chat session"
        mode: str = "simple"
        provider: str = "ollama"
        model: str = "llama3.2:latest"

    created_app = FastAPI(
        title="LLM Toolbox Universal Chat API",
        description="OpenAI/OpenWebUI-compatible REST API for any LLM provider",
        version="0.3.0",
    )

    @created_app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @created_app.get("/v1/models")
    def list_models() -> Dict[str, Any]:
        model_ids = [
            "llama3.2:latest",
            "gemini-1.5-flash",
            "mixtral-8x7b-32768",
            "deepseek-chat",
            "moonshot-v1-8k",
        ]
        return {
            "object": "list",
            "data": [
                {"id": mid, "object": "model", "created": int(time.time()), "owned_by": "llm_toolbox"}
                for mid in model_ids
            ],
        }

    @created_app.post("/v1/chat/completions")
    def chat_completions(request: ChatCompletionRequest) -> Dict[str, Any]:
        provider = request.provider or infer_provider_from_model(request.model)

        try:
            client = get_llm_client(provider=provider, model=request.model)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        history = [ChatMessage(role=m.role, content=m.content) for m in request.messages[:-1]]
        user_text = request.messages[-1].content if request.messages else ""

        selected_mode = resolve_mode(
            request.mode,
            rag_enabled=bool(request.rag_embed_provider) or request.rag_db_backend in {"chroma", "qdrant"},
        )
        mode_config = ChatModeConfig(
            mode=selected_mode,
            rag_embed_provider=request.rag_embed_provider,
            rag_db_backend=request.rag_db_backend,
            rag_collection=request.rag_collection,
            rag_top_k=request.rag_top_k,
        )

        conversation_id = request.conversation_id
        if not conversation_id:
            conv = CHAT_STORE.create_conversation(
                title="OpenWebUI/API session",
                mode=selected_mode,
                provider=provider,
                model=request.model,
                metadata={"interface": "api"},
            )
            conversation_id = conv.id

        if user_text:
            CHAT_STORE.add_message(conversation_id=conversation_id, role="user", content=user_text)

        try:
            content = generate_assistant_reply(
                user_text=user_text,
                history=history,
                llm_client=client,
                llm_provider=provider,
                mode_config=mode_config,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

        CHAT_STORE.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            metadata={"mode": selected_mode},
        )

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "conversation_id": conversation_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    @created_app.post("/v1/conversations")
    def create_conversation(request: ConversationCreateRequest) -> Dict[str, Any]:
        selected_mode = resolve_mode(request.mode, rag_enabled=True)
        conv = CHAT_STORE.create_conversation(
            title=request.title,
            mode=selected_mode,
            provider=request.provider,
            model=request.model,
            metadata={"interface": "api"},
        )
        return {
            "id": conv.id,
            "title": conv.title,
            "mode": conv.mode,
            "provider": conv.provider,
            "model": conv.model,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "metadata": conv.metadata,
        }

    @created_app.get("/v1/conversations")
    def list_conversations(limit: int = 50) -> Dict[str, Any]:
        items = CHAT_STORE.list_conversations(limit=limit)
        return {
            "object": "list",
            "data": [
                {
                    "id": item.id,
                    "title": item.title,
                    "mode": item.mode,
                    "provider": item.provider,
                    "model": item.model,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "metadata": item.metadata,
                }
                for item in items
            ],
        }

    @created_app.get("/v1/conversations/{conversation_id}/messages")
    def list_messages(conversation_id: str, limit: int = 500) -> Dict[str, Any]:
        messages = CHAT_STORE.get_messages(conversation_id=conversation_id, limit=limit)
        return {
            "object": "list",
            "data": [
                {
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                    "metadata": m.metadata,
                }
                for m in messages
            ],
        }

    app = created_app
    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError("uvicorn is required for web chat server features. Install with: pip install uvicorn") from exc

    web_app = ensure_web_app()
    print(f"Starting LLM Toolbox Chat Server on {host}:{port}")
    uvicorn.run(web_app, host=host, port=port, reload=reload)
