"""Provider-agnostic Self-RAG agent built with LangGraph.

Works standalone with langchain_adapters or alongside llm_toolbox/my_toolbox.
"""

from __future__ import annotations

from typing import List, TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from langchain_adapters import get_chat_model, get_embedding_model, supported_providers

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma


class AgentState(TypedDict):
    question: str
    documents: List[Document]
    generation: str
    reflection: str
    is_relevant: bool
    attempts: int


class SelfRAGAgent:
    """A simple reflection-based RAG agent with interchangeable providers."""

    def __init__(
        self,
        provider: str = "ollama",
        llm_model_name: str | None = None,
        embedding_model_name: str | None = None,
        temperature: float = 0.2,
        retriever_k: int = 4,
        max_attempts: int = 2,
        **provider_kwargs,
    ) -> None:
        self.provider = provider.strip().lower()
        if self.provider not in supported_providers():
            raise ValueError(
                f"Unsupported provider '{provider}'. Choose from: {', '.join(supported_providers())}"
            )

        self.temperature = temperature
        self.retriever_k = retriever_k
        self.max_attempts = max_attempts
        self.provider_kwargs = provider_kwargs

        self.llm = get_chat_model(
            self.provider,
            model=llm_model_name,
            temperature=temperature,
            **provider_kwargs,
        )
        self.embeddings = get_embedding_model(
            self.provider,
            model=embedding_model_name,
            **provider_kwargs,
        )
        self.vectorstore = None
        self.retriever = None
        self.graph = None

        self._build_rag_chain()
        self._build_reflection_chain()
        self._build_graph()

    def add_documents(self, texts: List[str], collection_name: str = "self_rag_agent") -> None:
        documents = [Document(page_content=text) for text in texts]
        if self.vectorstore:
            self.vectorstore.add_documents(documents)
        else:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
            )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.retriever_k})

    def _build_rag_chain(self) -> None:
        rag_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You answer questions using retrieved context. If the answer is not supported by the context, say you do not know.",
                ),
                ("user", "Question: {question}\nContext: {context}"),
            ]
        )
        self.rag_chain = rag_prompt | self.llm | StrOutputParser()

    def _build_reflection_chain(self) -> None:
        reflection_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Evaluate whether the answer fully addresses the question using only the supplied context. Respond with YES or NO on the first line, then a brief reason.",
                ),
                (
                    "user",
                    "Question: {question}\nContext: {context}\nGenerated Answer: {generation}\nDecision:",
                ),
            ]
        )
        self.reflection_chain = reflection_prompt | self.llm | StrOutputParser()

    def _build_graph(self) -> None:
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("generate", self._generate)
        workflow.add_node("reflect", self._reflect)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", "reflect")
        workflow.add_conditional_edges(
            "reflect",
            self._decide_to_end,
            {"end": END, "retrieve": "retrieve"},
        )
        self.graph = workflow.compile()

    def _retrieve(self, state: AgentState) -> AgentState:
        if self.retriever is None:
            raise ValueError("No documents added to the agent. Call add_documents() before invoke().")
        documents = self.retriever.invoke(state["question"])
        return {**state, "documents": documents}

    def _generate(self, state: AgentState) -> AgentState:
        context = "\n".join(doc.page_content for doc in state["documents"])
        generation = self.rag_chain.invoke({"question": state["question"], "context": context})
        return {**state, "generation": generation}

    def _reflect(self, state: AgentState) -> AgentState:
        context = "\n".join(doc.page_content for doc in state["documents"])
        reflection = self.reflection_chain.invoke(
            {
                "question": state["question"],
                "context": context,
                "generation": state["generation"],
            }
        )
        decision = reflection.strip().splitlines()[0].strip().upper()
        return {
            **state,
            "reflection": reflection,
            "is_relevant": decision.startswith("YES"),
            "attempts": state["attempts"] + 1,
        }

    def _decide_to_end(self, state: AgentState) -> str:
        if state["is_relevant"] or state["attempts"] >= self.max_attempts:
            return "end"
        return "retrieve"

    def invoke(self, question: str) -> AgentState:
        if self.graph is None:
            raise ValueError("Agent graph is not compiled")
        initial_state: AgentState = {
            "question": question,
            "documents": [],
            "generation": "",
            "reflection": "",
            "is_relevant": False,
            "attempts": 0,
        }
        return self.graph.invoke(initial_state)


__all__ = ["SelfRAGAgent", "supported_providers"]