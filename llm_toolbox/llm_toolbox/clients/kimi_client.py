"""Kimi/Moonshot LLM client (native provider, no LangChain dependency).

Kimi API: https://api.moonshot.cn
Also known as Moonshot. OpenAI-compatible API.
"""

import os
from typing import List, Iterator
from . import ChatMessage


class KimiLLMClient:
    """Native Kimi/Moonshot LLM client using REST API (OpenAI-compatible)."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ):
        """Initialize Kimi client.
        
        Args:
            model: Model name (e.g., "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k")
            api_key: Kimi API key (reads from KIMI_API_KEY if not provided)
            base_url: Kimi API base URL (default: https://api.moonshot.cn/v1)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
        """
        self.model = model or os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = (base_url or os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")).rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = "kimi"

        if not self.api_key:
            raise ValueError(
                "Kimi API key not found. "
                "Set KIMI_API_KEY environment variable or pass api_key parameter."
            )

    def complete(self, messages: List[ChatMessage]) -> str:
        """Get a completion from Kimi (OpenAI-compatible).
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            Response text
        """
        import urllib.request
        import json

        # Convert ChatMessage to API format
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature,
            "stream": False,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Kimi API error: {e.read().decode()}")

    def stream(self, messages: List[ChatMessage]) -> Iterator[str]:
        """Stream a completion from Kimi (OpenAI-compatible).
        
        Args:
            messages: List of ChatMessage objects
            
        Yields:
            Response chunks
        """
        import urllib.request
        import json

        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature,
            "stream": True,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    line = line.decode().strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content is not None:
                                    yield content
                        except json.JSONDecodeError:
                            pass
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Kimi API error: {e.read().decode()}")
