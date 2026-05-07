"""Deepseek LLM client (native provider, no LangChain dependency).

Deepseek API: https://api.deepseek.com
Supports chat completions with streaming.
"""

import os
from typing import List, Optional, Iterator
from . import ChatMessage


class DeepseekLLMClient:
    """Native Deepseek LLM client using REST API."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ):
        """Initialize Deepseek client.
        
        Args:
            model: Model name (e.g., "deepseek-chat")
            api_key: Deepseek API key (reads from DEEPSEEK_API_KEY if not provided)
            base_url: Deepseek API base URL (default: https://api.deepseek.com/v1)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
        """
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")).rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = "deepseek"

        if not self.api_key:
            raise ValueError(
                "Deepseek API key not found. "
                "Set DEEPSEEK_API_KEY environment variable or pass api_key parameter."
            )

    def complete(self, messages: List[ChatMessage]) -> str:
        """Get a completion from Deepseek.
        
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
            raise RuntimeError(f"Deepseek API error: {e.read().decode()}")

    def stream(self, messages: List[ChatMessage]) -> Iterator[str]:
        """Stream a completion from Deepseek.
        
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
            raise RuntimeError(f"Deepseek API error: {e.read().decode()}")
