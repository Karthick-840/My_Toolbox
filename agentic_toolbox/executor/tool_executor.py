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