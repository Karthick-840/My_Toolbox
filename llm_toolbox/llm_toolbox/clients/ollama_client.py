"""Local Ollama adapter implementing the shared LLM client contract."""

from __future__ import annotations

import json
import urllib.request
from typing import Iterable, List

from llm_toolbox.clients import BaseLLMClient, ChatMessage


class OllamaLLMClient(BaseLLMClient):
    provider = "ollama"

    def __init__(self, model: str = "llama3.2:latest", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "options": {"temperature": temperature},
            "stream": False,
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310
            raw = resp.read().decode("utf-8")
        body = json.loads(raw)
        return body.get("message", {}).get("content", "")

    def stream(self, messages: List[ChatMessage], temperature: float = 0.2) -> Iterable[str]:
        payload = {
            "model": self.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "options": {"temperature": temperature},
            "stream": True,
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310
            for line in resp:
                if not line:
                    continue
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("message", {}).get("content")
                if token:
                    yield token
