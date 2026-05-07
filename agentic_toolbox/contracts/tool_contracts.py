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