# Phase 0-1 Bootstrap: Contracts & Registry Skeleton

Use this as your starting point for implementing `agentic_toolbox` infrastructure.

## File 1: agentic_toolbox/contracts/tool_contracts.py

```python
"""Tool contract definitions (protocol-agnostic).

This module defines the contracts that MCP, A2A, and local orchestrators
(Pydantic-AI, LangGraph) all conform to.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolTag(str, Enum):
    """Safety and capability tags for tools."""
    READ = "read"              # Read-only file/data access
    WRITE = "write"            # File/data modification
    EXEC = "exec"              # Command/code execution
    NETWORK = "network"        # Network calls
    DANGEROUS = "dangerous"    # Requires extra approval
    SAFE = "safe"              # Safe for untrusted users


class ToolInputSchema(BaseModel):
    """Schema for tool input parameters."""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolOutputSchema(BaseModel):
    """Schema for tool output."""
    type: str = "string"
    description: str = ""


@dataclass
class ToolPolicy:
    """Runtime policy for tool execution."""
    tags: List[ToolTag] = field(default_factory=list)
    max_timeout_secs: int = 60
    max_output_chars: int = 100_000
    allowed_patterns: List[str] = field(default_factory=list)  # Regex allowlists
    denied_patterns: List[str] = field(default_factory=list)   # Regex denylists
    requires_auth: bool = False
    quota_per_hour: Optional[int] = None


@dataclass
class ToolSpec:
    """Complete tool specification (protocol-independent)."""
    name: str
    description: str
    input_schema: ToolInputSchema
    output_schema: ToolOutputSchema
    policy: ToolPolicy
    version: str = "1.0.0"
    handler: Optional[Callable] = None  # Runtime handler function


@dataclass
class ExecutionContext:
    """Context passed to every tool invocation."""
    user_id: str = "unknown"
    tenant_id: str = "default"
    correlation_id: str = ""
    workspace_root: Optional[str] = None
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolInvocation:
    """A request to invoke a tool."""
    tool_name: str
    arguments: Dict[str, Any]
    context: ExecutionContext
    request_id: str = ""  # Unique per invocation


@dataclass
class ToolResult:
    """Result of a tool invocation."""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    request_id: str = ""
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
```

## File 2: agentic_toolbox/registry/tool_registry.py

```python
"""Central tool registry and discovery."""

from typing import Dict, List, Optional, Callable
from agentic_toolbox.contracts.tool_contracts import (
    ToolSpec, ToolInvocation, ToolResult, ExecutionContext, ToolTag, ToolPolicy
)


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(self, spec: ToolSpec, handler: Callable) -> None:
        """Register a tool with its handler.
        
        Args:
            spec: Tool specification
            handler: Callable that executes the tool
        
        Raises:
            ValueError: If tool already exists or spec is invalid
        """
        if spec.name in self._tools:
            raise ValueError(f"Tool '{spec.name}' already registered")
        
        self._tools[spec.name] = spec
        self._handlers[spec.name] = handler

    def list_tools(self, tags: Optional[List[ToolTag]] = None) -> List[ToolSpec]:
        """List all registered tools, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by (AND logic)
        
        Returns:
            List of matching ToolSpecs
        """
        results = list(self._tools.values())
        
        if tags:
            results = [
                t for t in results
                if all(tag in t.policy.tags for tag in tags)
            ]
        
        return results

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        """Get a tool spec by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    async def invoke(self, invocation: ToolInvocation) -> ToolResult:
        """Invoke a tool by name with arguments.
        
        This is a thin wrapper; actual policy enforcement happens in executor.
        
        Args:
            invocation: Tool invocation request
        
        Returns:
            ToolResult with execution status and output
        """
        if not self.has_tool(invocation.tool_name):
            return ToolResult(
                tool_name=invocation.tool_name,
                success=False,
                output=None,
                error=f"Tool '{invocation.tool_name}' not found",
                request_id=invocation.request_id,
            )

        handler = self._handlers[invocation.tool_name]
        
        try:
            output = await handler(invocation.arguments, invocation.context)
            return ToolResult(
                tool_name=invocation.tool_name,
                success=True,
                output=output,
                request_id=invocation.request_id,
            )
        except Exception as e:
            return ToolResult(
                tool_name=invocation.tool_name,
                success=False,
                output=None,
                error=str(e),
                request_id=invocation.request_id,
            )


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
```

## File 3: agentic_toolbox/executor/tool_executor.py

```python
"""Tool execution with policy enforcement and safety."""

import asyncio
from typing import Dict, Any
from agentic_toolbox.contracts.tool_contracts import (
    ToolInvocation, ToolResult, ToolPolicy, ToolTag
)
from agentic_toolbox.registry.tool_registry import get_registry


class ToolExecutor:
    """Executes tools with policy checks and safety enforcement."""

    def __init__(self, registry=None):
        self.registry = registry or get_registry()

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        """Execute a tool with full policy enforcement.
        
        Args:
            invocation: Tool invocation request
        
        Returns:
            ToolResult with execution details and audit metadata
        """
        tool_spec = self.registry.get_tool(invocation.tool_name)
        
        if not tool_spec:
            return ToolResult(
                tool_name=invocation.tool_name,
                success=False,
                output=None,
                error=f"Tool not found: {invocation.tool_name}",
                request_id=invocation.request_id,
            )

        # Policy checks
        policy_result = self._check_policy(tool_spec.policy, invocation)
        if not policy_result["allowed"]:
            return ToolResult(
                tool_name=invocation.tool_name,
                success=False,
                output=None,
                error=f"Policy violation: {policy_result['reason']}",
                request_id=invocation.request_id,
                audit_metadata={"policy_violation": policy_result["reason"]},
            )

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self.registry.invoke(invocation),
                timeout=tool_spec.policy.max_timeout_secs
            )
            
            # Add audit metadata
            result.audit_metadata = {
                "user_id": invocation.context.user_id,
                "tenant_id": invocation.context.tenant_id,
                "correlation_id": invocation.context.correlation_id,
                "tool_tags": [tag.value for tag in tool_spec.policy.tags],
            }
            
            return result
        
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=invocation.tool_name,
                success=False,
                output=None,
                error=f"Tool execution timeout ({tool_spec.policy.max_timeout_secs}s)",
                request_id=invocation.request_id,
                audit_metadata={"timeout": tool_spec.policy.max_timeout_secs},
            )

    def _check_policy(self, policy: ToolPolicy, invocation: ToolInvocation) -> Dict[str, Any]:
        """Check if invocation complies with tool policy.
        
        Returns:
            {"allowed": bool, "reason": str}
        """
        # Example: Check DANGEROUS tag
        if ToolTag.DANGEROUS in policy.tags and invocation.context.user_id == "unknown":
            return {"allowed": False, "reason": "Dangerous tools require authenticated user"}

        # Example: Check quota
        if policy.quota_per_hour and invocation.context.metadata.get("quota_used", 0) >= policy.quota_per_hour:
            return {"allowed": False, "reason": "Quota exceeded for this hour"}

        return {"allowed": True, "reason": ""}
```

## File 4: agentic_toolbox/__init__.py

```python
"""Agentic toolbox: protocol-agnostic tool runtime."""

from agentic_toolbox.contracts.tool_contracts import (
    ToolSpec,
    ToolTag,
    ToolPolicy,
    ToolInvocation,
    ToolResult,
    ExecutionContext,
)
from agentic_toolbox.registry.tool_registry import ToolRegistry, get_registry
from agentic_toolbox.executor.tool_executor import ToolExecutor

__all__ = [
    "ToolSpec",
    "ToolTag",
    "ToolPolicy",
    "ToolInvocation",
    "ToolResult",
    "ExecutionContext",
    "ToolRegistry",
    "get_registry",
    "ToolExecutor",
]
```

## File 5: agentic_toolbox/tests/test_registry.py

```python
"""Tests for tool registry."""

import pytest
from agentic_toolbox.contracts.tool_contracts import (
    ToolSpec, ToolInputSchema, ToolOutputSchema, ToolPolicy, ToolTag
)
from agentic_toolbox.registry.tool_registry import ToolRegistry


def dummy_handler(args, context):
    """Dummy handler for testing."""
    return args.get("value", "default")


def test_register_tool():
    """Test registering a tool."""
    registry = ToolRegistry()
    
    spec = ToolSpec(
        name="test_tool",
        description="A test tool",
        input_schema=ToolInputSchema(properties={"value": {"type": "string"}}),
        output_schema=ToolOutputSchema(type="string", description="Test output"),
        policy=ToolPolicy(tags=[ToolTag.SAFE]),
    )
    
    registry.register(spec, dummy_handler)
    assert registry.has_tool("test_tool")
    assert registry.get_tool("test_tool").name == "test_tool"


def test_list_tools_by_tag():
    """Test filtering tools by tag."""
    registry = ToolRegistry()
    
    safe_spec = ToolSpec(
        name="safe_tool",
        description="Safe",
        input_schema=ToolInputSchema(),
        output_schema=ToolOutputSchema(),
        policy=ToolPolicy(tags=[ToolTag.SAFE]),
    )
    
    dangerous_spec = ToolSpec(
        name="dangerous_tool",
        description="Dangerous",
        input_schema=ToolInputSchema(),
        output_schema=ToolOutputSchema(),
        policy=ToolPolicy(tags=[ToolTag.DANGEROUS]),
    )
    
    registry.register(safe_spec, dummy_handler)
    registry.register(dangerous_spec, dummy_handler)
    
    safe_tools = registry.list_tools(tags=[ToolTag.SAFE])
    assert len(safe_tools) == 1
    assert safe_tools[0].name == "safe_tool"
```

## Setup Instructions

### 1. Create directory structure
```bash
mkdir -p agentic_toolbox/contracts
mkdir -p agentic_toolbox/registry
mkdir -p agentic_toolbox/executor
mkdir -p agentic_toolbox/protocols
mkdir -p agentic_toolbox/tests
```

### 2. Copy files above into respective modules

### 3. Install dev dependencies
```bash
cd agentic_toolbox
pip install pydantic pytest pytest-asyncio
```

### 4. Run tests
```bash
pytest agentic_toolbox/tests/test_registry.py -v
```

### 5. Push to main and GitHub Actions will validate

The workflow in `.github/workflows/agentic-langchain-ci.yml` will now:
- ✓ Lint these new modules
- ✓ Run contract conformance checks
- ✓ Run unit tests
- Post status to PRs

---

**Next Steps**
1. Adapt these files to your exact style preferences
2. Create `agentic_toolbox/executor/tool_executor.py` with actual policy logic
3. Create `agentic_toolbox/protocols/mcp_server.py` to expose registry via MCP (Phase 3)
4. Port existing `CodingTools` methods into registry handlers
