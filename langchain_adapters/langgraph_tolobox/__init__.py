"""LangGraph toolbox exports."""

__all__ = ["SelfRAGAgent"]


def __getattr__(name: str):
	if name == "SelfRAGAgent":
		from .self_rag_agent import SelfRAGAgent

		return SelfRAGAgent
	raise AttributeError(name)