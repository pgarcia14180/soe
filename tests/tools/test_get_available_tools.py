import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_get_available_tools import create_soe_get_available_tools_tool
from soe.builtin_tools import BUILTIN_TOOLS

def test_soe_get_available_tools_no_user_tools():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    get_tool = create_soe_get_available_tools_tool(execution_id, backends)

    result = get_tool()

    assert "builtin_tools" in result
    assert "user_tools" in result
    assert result["user_tools"] == []

    # Check that all builtin tools are present
    for tool_name in BUILTIN_TOOLS:
        assert tool_name in result["builtin_tools"]

def test_soe_get_available_tools_with_user_tools():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    user_tools = {
        "my_custom_tool": lambda x: x,
        "another_tool": lambda y: y
    }

    get_tool = create_soe_get_available_tools_tool(execution_id, backends, tools_registry=user_tools)

    result = get_tool()

    assert "builtin_tools" in result
    assert "user_tools" in result
    assert len(result["user_tools"]) == 2
    assert "my_custom_tool" in result["user_tools"]
    assert "another_tool" in result["user_tools"]
