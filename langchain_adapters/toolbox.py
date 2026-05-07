"""Reusable LangChain toolbox with provider-aware chat and retrieval helpers."""

from __future__ import annotations

from typing import Iterable, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .provider_factory import get_chat_model, get_embedding_model, supported_providers

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma


class LangChainToolbox:
    """Simple provider-agnostic RAG helper for LangChain workflows."""

    def __init__(
        self,
        provider: str = "ollama",
        chat_model: str | None = None,
        embedding_model: str | None = None,
        temperature: float = 0.2,
        retriever_k: int = 4,
        collection_name: str = "langchain_toolbox",
        **provider_kwargs,
    ) -> None:
        key = provider.strip().lower()
        if key not in supported_providers():
            raise ValueError(
                f"Unsupported provider '{provider}'. Choose from: {', '.join(supported_providers())}"
            )

        self.provider = key
        self.collection_name = collection_name
        self.retriever_k = retriever_k
        self.chat = get_chat_model(key, model=chat_model, temperature=temperature, **provider_kwargs)
        self.embeddings = get_embedding_model(key, model=embedding_model, **provider_kwargs)
        self.vectorstore = None
        self.retriever = None

    def ingest_texts(self, texts: Iterable[str]) -> int:
        documents = [Document(page_content=text) for text in texts]
        if not documents:
            return 0

        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.collection_name,
            )
        else:
            self.vectorstore.add_documents(documents)

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.retriever_k})
        return len(documents)

    def ask(self, question: str, system_prompt: str | None = None) -> str:
        if self.retriever is None:
            raise ValueError("No data ingested. Call ingest_texts() before ask().")

        retrieved_docs: List[Document] = self.retriever.invoke(question)
        context = "\n".join(doc.page_content for doc in retrieved_docs)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt
                    or "Use the supplied context to answer the question. If the answer is not supported by the context, say you do not know.",
                ),
                ("user", "Question: {question}\nContext: {context}"),
            ]
        )
        chain = prompt | self.chat | StrOutputParser()
        return chain.invoke({"question": question, "context": context})


__all__ = ["LangChainToolbox"]