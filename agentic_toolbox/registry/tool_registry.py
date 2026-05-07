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