"""Groq adapter implementing the shared LLM client contract."""

from __future__ import annotations

import os
from typing import List, Iterable

from llm_toolbox.clients import BaseLLMClient, ChatMessage


class GroqLLMClient(BaseLLMClient):
    """Groq client with low-latency LLM inference."""

    provider = "groq"

    def __init__(self, model: str = "mixtral-8x7b-32768", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for GroqLLMClient")

        try:
            from langchain_groq import ChatGroq
            from langchain_core.prompts import ChatPromptTemplate
        except ImportError as exc:
            raise ImportError("langchain-groq is required for GroqLLMClient") from exc

        self._groq = ChatGroq(
            temperature=0,
            model_name=model,
            groq_api_key=self.api_key,
        )
        self._ChatPromptTemplate = ChatPromptTemplate

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        """Return a single completion."""
        prompt_messages = [(m.role, m.content) for m in messages]
        prompt = self._ChatPromptTemplate.from_messages(prompt_messages)
        chain = prompt | self._groq
        response = chain.invoke({})
        return response.content

    def stream(self, messages: List[ChatMessage], temperature: float = 0.2) -> Iterable[str]:
        """Stream tokens from the model."""
        prompt_messages = [(m.role, m.content) for m in messages]
        prompt = self._ChatPromptTemplate.from_messages(prompt_messages)
        chain = prompt | self._groq
        for chunk in chain.stream({}):
            yield chunk.content if hasattr(chunk, "content") else str(chunk)
