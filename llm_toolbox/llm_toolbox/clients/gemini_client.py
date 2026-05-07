"""Gemini adapter implementing the shared LLM client contract."""

from __future__ import annotations

import json
import os
from typing import List

from llm_toolbox.clients import BaseLLMClient, ChatMessage


class GeminiLLMClient(BaseLLMClient):
    provider = "gemini"

    def __init__(self, model: str = "gemini-1.5-flash", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for GeminiLLMClient")

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError("google-generativeai is required for GeminiLLMClient") from exc

        genai.configure(api_key=self.api_key)
        self._genai = genai

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        system_parts = [m.content for m in messages if m.role == "system"]
        user_parts = [m.content for m in messages if m.role != "system"]
        system_prefix = "\n\n".join(system_parts)
        user_prompt = "\n\n".join(user_parts)

        prompt = user_prompt if not system_prefix else f"SYSTEM:\n{system_prefix}\n\nUSER:\n{user_prompt}"
        model = self._genai.GenerativeModel(
            self.model,
            generation_config={"temperature": temperature},
        )
        response = model.generate_content(prompt)
        return getattr(response, "text", "") or ""


class GeminiModelInfo:
    """Utility class for exploring and managing Gemini models.

    Independent of GeminiLLMClient — provides model caching, listing, and info.
    """

    _is_configured = False

    def __init__(self, api_key: str | None = None, gen_config: dict | None = None) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError("google-generativeai required for GeminiModelInfo") from exc

        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY required for GeminiModelInfo")

        genai.configure(api_key=api_key)
        self._genai = genai

        if not GeminiModelInfo._is_configured:
            GeminiModelInfo._is_configured = True

        self.gen_config = gen_config or {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

    def list_models(self) -> list[str]:
        """List all available Gemini models."""
        return [m.name for m in self._genai.list_models()]

    def save_model_info_to_json(self, filename: str = "models_info.json") -> None:
        """Save all model metadata to JSON file."""
        all_models = {}
        for m in self._genai.list_models():
            model_info = m.__dict__.copy()
            model_info["type"] = (
                "Generative Model"
                if "generateContent" in m.supported_generation_methods
                else "Other Model"
            )
            all_models[m.name] = model_info

        with open(filename, "w") as f:
            json.dump(all_models, f, indent=4, default=str)

        print(f"Model info saved to {filename}")

