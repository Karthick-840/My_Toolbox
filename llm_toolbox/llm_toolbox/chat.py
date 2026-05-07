#!/usr/bin/env python3
"""Unified chat module.

This file provides:
- Chat class: Interactive chat session handler with optional persistence
- Chat mode orchestration (simple/rag/auto)  
- Server launcher
- Client builder utility
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from llm_toolbox.clients import ChatMessage, get_llm_client, resolve_chat_provider


@dataclass
class ChatModeConfig:
    mode: str = "simple"
    rag_embed_provider: Optional[str] = None
    rag_db_backend: str = "chroma"
    rag_collection: str = "documents"
    rag_top_k: int = 5


def normalize_mode(mode: str) -> str:
    key = mode.strip().lower()
    if key in {"simple", "rag", "auto"}:
        return key
    raise ValueError(f"Unsupported mode: {mode}. Choose from: simple, rag, auto")


def resolve_mode(mode: str, rag_enabled: bool) -> str:
    key = normalize_mode(mode)
    if key != "auto":
        return key
    return "rag" if rag_enabled else "simple"


def generate_assistant_reply(
    *,
    user_text: str,
    history: List[ChatMessage],
    llm_client: Any,
    llm_provider: str,
    mode_config: ChatModeConfig,
) -> str:
    selected_mode = mode_config.mode

    if selected_mode == "simple":
        messages = list(history)
        messages.append(ChatMessage(role="user", content=user_text))
        return llm_client.complete(messages)

    if selected_mode == "rag":
        from llm_toolbox.query_rag import query_rag

        return query_rag(
            user_text,
            embed_provider=mode_config.rag_embed_provider,
            db_backend=mode_config.rag_db_backend,
            llm_provider=llm_provider,
            collection=mode_config.rag_collection,
            top_k=mode_config.rag_top_k,
        )

    raise ValueError(f"Invalid chat mode: {selected_mode}")


def build_chat_client(
    *,
    model: str,
    endpoint: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
):
    """Create an LLM client from a direct model/endpoint/api_key tuple.

    This is the thin path for scripts/examples that do not want provider maps.
    """
    selected = resolve_chat_provider(model=model, endpoint=endpoint, provider=provider)
    kwargs: Dict[str, Any] = {}
    if endpoint:
        kwargs["base_url"] = endpoint
    if api_key:
        kwargs["api_key"] = api_key
    return get_llm_client(provider=selected, model=model, **kwargs)


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Launch the FastAPI web server for chat API."""
    from llm_toolbox.webui import run_server as webui_run_server

    webui_run_server(host=host, port=port, reload=reload)


# ── Chat Class ─────────────────────────────────────────────────────────────────

class Chat:
    """Interactive chat session handler with optional persistence.
    
    Supports streaming replies, simple/RAG modes, and conversation storage.
    """
    
    def __init__(
        self,
        client,
        *,
        system_prompt: str = "",
        debug_stream: bool = False,
        quit_commands=("quit", "exit", "bye"),
    ):
        """Initialize chat session.
        
        Args:
            client: LLM client instance
            system_prompt: System message for the assistant
            debug_stream: If True, print debug markers between tokens
            quit_commands: Tuple of commands that end the chat
        """
        self.client = client
        self.system_prompt = system_prompt
        self.debug_stream = debug_stream
        self.quit_commands = quit_commands
    
    def stream_reply(self, messages) -> str:
        """Stream an LLM response to stdout token-by-token.

        Handles:
        - <think>...</think> blocks from reasoning models (suppressed from display)
        - 429 rate-limit errors (friendly message, returns "")
        - None chunks from some providers
        """
        chunks = []
        in_think = False
        try:
            for chunk in self.client.stream(messages):
                if chunk is None:
                    continue
                if "<think>" in chunk:
                    in_think = True
                if in_think:
                    chunks.append(chunk)
                    if "</think>" in chunk:
                        in_think = False
                    continue
                print(chunk, end="|" if self.debug_stream else "", flush=True)
                chunks.append(chunk)
        except RuntimeError as exc:
            msg = str(exc)
            if "429" in msg or "too many requests" in msg.lower():
                print("\n[Rate limited — wait a moment and try again]")
                return ""
            raise
        print()
        full = "".join(chunks)
        return re.sub(r"<think>.*?</think>", "", full, flags=re.DOTALL).strip()
    
    def run(
        self,
        *,
        persist: bool = False,
        store=None,
        conversation_id: str | None = None,
    ) -> None:
        """Start interactive chat session with optional persistence.
        
        Args:
            persist: If True, save/load messages from store
            store: Chat store instance (required if persist=True)
            conversation_id: Conversation ID (required if persist=True)
            
        Raises:
            ValueError: If persist=True but store or conversation_id is None
        """
        if persist and (store is None or conversation_id is None):
            raise ValueError("persist=True requires store and conversation_id")

        history = []

        def _build(user_text: str):
            msgs = []
            if self.system_prompt:
                msgs.append(ChatMessage(role="system", content=self.system_prompt))
            if persist:
                for rec in store.get_messages(conversation_id):
                    msgs.append(ChatMessage(role=rec.role, content=rec.content))
            else:
                msgs.extend(history)
            msgs.append(ChatMessage(role="user", content=user_text))
            return msgs

        # Send welcome message
        print("Assistant: ", end="", flush=True)
        welcome = self.stream_reply(_build("Give a short welcome message and what you can help with."))
        if welcome:
            if persist:
                store.add_message(conversation_id=conversation_id, role="assistant", content=welcome)
            else:
                history.append(ChatMessage(role="assistant", content=welcome))
        print()

        # Main chat loop
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[Chat ended]")
                break
            if not user_input:
                continue
            if user_input.lower() in self.quit_commands:
                print("[Chat ended]")
                break

            # Save user message
            if persist:
                store.add_message(conversation_id=conversation_id, role="user", content=user_input)
            else:
                history.append(ChatMessage(role="user", content=user_input))

            # Get and save assistant reply
            print("Assistant: ", end="", flush=True)
            reply = self.stream_reply(_build(user_input))
            if reply:
                if persist:
                    store.add_message(conversation_id=conversation_id, role="assistant", content=reply)
                else:
                    history.append(ChatMessage(role="assistant", content=reply))
            print()

        # Print session summary if persisted
        if persist:
            total = len(store.get_messages(conversation_id))
            print(f"Conversation id : {conversation_id}")
            print(f"Messages saved  : {total}")
