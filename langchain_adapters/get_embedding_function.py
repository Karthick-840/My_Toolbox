"""DEPRECATED: Use core llm_toolbox.embeddings module instead.

This module is kept for backward compatibility only.

MIGRATION:
  OLD (LangChain-based): from llm_toolbox.get_embedding_function import get_embedding_function
  NEW (provider-native):  from llm_toolbox.embeddings import get_embedder

The new provider-native approach (embeddings.get_embedder) returns BaseEmbedder objects
with zero LangChain dependency, while this module still uses LangChain for interop.

For new code, use:
    from llm_toolbox.embeddings import get_embedder
    embedder = get_embedder("ollama")
    vecs = embedder.embed_documents(documents)

For LangChain interop (legacy), use langchain_adapters:
    from llm_toolbox.langchain_adapters.embeddings import get_langchain_embeddings
    embed_fn = get_langchain_embeddings("ollama")
"""

import warnings

def get_embedding_function(provider=None, model=None, **kwargs):
    """DEPRECATED: Use llm_toolbox.embeddings.get_embedder() instead.
    
    This function is kept for backward compatibility. It forwards to the
    LangChain adapter module.
    """
    warnings.warn(
        "get_embedding_function() is deprecated. "
        "Use llm_toolbox.embeddings.get_embedder() for provider-native embeddings, "
        "or llm_toolbox.langchain_adapters.embeddings.get_langchain_embeddings() for LangChain interop.",
        DeprecationWarning,
        stacklevel=2
    )
    from .embeddings import get_langchain_embeddings
    return get_langchain_embeddings(provider=provider, model=model, **kwargs)