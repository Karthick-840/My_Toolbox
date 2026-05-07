# Agentic Toolbox Implementation Plan

## 1. Goal
Build `agentic_toolbox` as a protocol-and-tools runtime that depends on `llm_toolbox` for model/chat/RAG client access.

## 2. Responsibility Boundaries
- `llm_toolbox`
  - Provider clients and routing
  - Chat + RAG core features
  - Embeddings and vector DB integrations
  - Conversation persistence
- `agentic_toolbox`
  - Tool contracts, tool registry, tool executor
  - MCP server exposure
  - A2A task protocol exposure
  - Policy enforcement, auth, audit, quotas

Do not duplicate provider logic in `agentic_toolbox`.

## 3. Target Architecture
1. `contracts/`
- `ToolSpec`
- `ToolInputSchema`
- `ToolOutputSchema`
- `ToolInvocation`
- `ToolResult`
- `ExecutionContext`

2. `registry/`
- Central tool registry with discover + validate + invoke APIs
- Tool metadata tags: `read`, `write`, `exec`, `network`, `dangerous`

3. `executor/`
- Workspace boundary checks
- Command allowlist
- Timeout + max output caps
- Retry policy for transient failures

4. `protocols/mcp/`
- `list_tools`
- `call_tool`
- Capability descriptors and schemas

5. `protocols/a2a/`
- `submit_task`
- `task_status`
- `task_result`
- Event stream with correlation IDs

6. `orchestrators/`
- Pydantic-AI / LangGraph adapters consuming the registry
- No inline tool definitions inside orchestrator setup

## 4. Migration Plan
## Phase 0: Stabilize Existing Runtime
- Fix import surface mismatches to point to `llm_toolbox` canonical paths
- Add tests around current `CodingTools` behavior
- Add a strict command policy profile (`safe`, `balanced`, `extended`)

## Phase 1: Extract Contracts
- Introduce typed contracts for tool IO and context
- Wrap current coding tool methods as contract-compliant handlers

## Phase 2: Add Registry + Executor
- Add centralized registry for all tools
- Route every tool call through policy-aware executor
- Add per-tool metrics and structured logs

## Phase 3: MCP MVP
- Expose registry over MCP
- Add schema validation and standardized errors
- Validate using one external MCP client

## Phase 4: A2A MVP
- Add asynchronous task runtime and status transitions
- Add cancellation and timeout states
- Persist task state to lightweight DB

## Phase 5: Production Hardening
- AuthN/AuthZ for tool classes
- Quotas and budget caps
- Audit sink integration
- Multi-tenant namespace separation

## 5. Automation (No Manual Intervention)
## CI (per PR)
1. Lint/type/test all changed modules
2. Contract conformance tests for all tool specs
3. Security scans: dependency + command-policy lint
4. Protocol integration tests (MCP + A2A smoke)

## CD (post-merge)
1. Build versioned image
2. Run migration checks
3. Deploy canary
4. Execute synthetic MCP/A2A calls
5. Promote automatically if SLOs pass

## Runtime Automation
- Scheduled health probes for provider reachability
- Auto-disable unhealthy tools via feature flags
- Auto-rotate fallbacks for llm providers based on error budget

## 6. Guardrails
## Input Guardrails
- Schema validation for every invocation
- Max payload size and depth limits
- Block unsafe shell tokens for exec tools

## Execution Guardrails
- Workspace path jail
- Command allowlist + denylist patterns
- CPU/time/output limits
- Network egress policy by tool tag

## Output Guardrails
- PII redaction hooks
- Secret scanning before returning responses
- Sensitive file path masking

## Operational Guardrails
- Per-user and per-tenant quotas
- Circuit breakers for unstable providers
- Mandatory audit trail: who invoked what, with which inputs

## 7. Repository Layout Recommendation
```text
agentic_toolbox/
  contracts/
    tool_contracts.py
  registry/
    tool_registry.py
  executor/
    tool_executor.py
    policy.py
  protocols/
    mcp_server.py
    a2a_server.py
  orchestrators/
    pydantic_adapter.py
    langgraph_adapter.py
  config/
    settings.py
  tests/
    test_registry.py
    test_executor_policy.py
    test_mcp_smoke.py
    test_a2a_smoke.py
```

## 8. Definition of Done
- New tool addition requires only: one contract + one handler + one registry entry
- MCP and A2A return identical behavior for same tool call
- All calls are policy-checked and auditable
- llm backend switching remains in `llm_toolbox` only
