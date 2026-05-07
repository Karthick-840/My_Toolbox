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