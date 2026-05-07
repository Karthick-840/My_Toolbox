# LangChain Toolbox Implementation Plan

## 1. Goal
Build `langchain_adapters` as a framework adapter layer that uses `llm_toolbox` as backend and can optionally consume `agentic_toolbox` tools.

## 2. Dependency Rules
- Allowed
  - `langchain_adapters` -> `llm_toolbox`
  - `langchain_adapters` -> `agentic_toolbox` contracts (thin dependency only)
- Not allowed
  - `llm_toolbox` importing LangChain classes
  - Circular dependency from `agentic_toolbox` back to `langchain_adapters`

Keep framework-specific code in adapters only.

## 3. Target Capability Set
1. LLM Wrapper Layer
- Build LangChain chat model wrappers from `llm_toolbox` provider clients
- Provider selection still resolved through `llm_toolbox`

2. Retriever Layer
- LangChain retriever adapters over `llm_toolbox` vector stores
- Configurable top-k, filters, hybrid scoring options

3. Chain Templates
- Q&A chain
- Retrieval chain
- Tool-augmented chain (calls `agentic_toolbox` registry)
- Summarization chain

4. Memory Adapters
- Optional bridge to conversation persistence in `llm_toolbox`
- Session, conversation, tenant-scoped memory backends

5. Evaluation Harness
- Prompt and chain regression tests
- Latency + correctness metrics

## 4. Concrete Module Design
```text
langchain_adapters/
  bridge/
    llm_wrapper.py
    embedding_wrapper.py
    retriever_wrapper.py
  chains/
    qa_chain.py
    rag_chain.py
    summarize_chain.py
    tool_call_chain.py
  memory/
    chat_history_memory.py
  eval/
    chain_eval.py
  config/
    chain_profiles.py
  tests/
    test_wrappers.py
    test_chains.py
    test_memory_bridge.py
```

## 5. Implementation Phases
## Phase 0: Core Wrappers
- Standardize wrappers for chat and embeddings over `llm_toolbox`
- Add compatibility matrix per provider

## Phase 1: Retrieval + RAG Chains
- Plug retriever wrappers into LangChain pipeline
- Add retrieval quality tests

## Phase 2: Tool-Calling Integration
- Adapter to invoke `agentic_toolbox` registry tools from LangChain chains
- Add structured tool result handling

## Phase 3: Memory + Context
- Bridge LangChain memory to `llm_toolbox` chat history
- Add conversation replay support

## Phase 4: Eval + Production Profiles
- Add benchmark harness
- Create profile presets: `local_dev`, `cloud_fast`, `high_quality`

## 6. Automation (No Manual Intervention)
## CI (per PR)
1. Wrapper contract tests
2. Chain integration tests with mocked providers
3. Real-provider nightly test matrix (Ollama/Gemini/Groq as available)
4. Prompt regression tests against fixed dataset

## CD
1. Build + publish package artifact
2. Run post-deploy synthetic chain runs
3. Auto-rollback if latency/error thresholds fail

## Runtime Automation
- Adaptive provider routing by latency and error rate
- Automatic fallback chain profile if retrieval fails
- Scheduled re-index jobs for stale RAG corpora

## 7. Guardrails
## Chain Guardrails
- Max intermediate steps
- Max tool calls per run
- Loop detection and forced termination

## Prompt Guardrails
- Prompt template linting for unsafe placeholders
- Output schema enforcement with strict parsers

## Data Guardrails
- Source allowlists for ingestion
- Metadata filters to prevent cross-tenant leakage
- PII/secret scan on retrieved context

## 8. Interop with Agentic Toolbox
Use thin shared contracts:
- `ToolSpec`
- `ToolInvocation`
- `ToolResult`

LangChain adapter should call tool registry APIs, not direct shell/file primitives.

## 9. Definition of Done
- LangChain workflows can switch providers without code changes
- Tool calls are delegated to `agentic_toolbox` registry with guardrails
- Memory uses `llm_toolbox` persistence contracts
- CI includes wrapper, chain, and regression validations
