"""
Tests for get_context builtin tool.
"""

import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_get_context import create_soe_get_context_tool


def test_get_context_all_fields():
    """Test getting all context fields."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup context with some fields
    backends.context.save_context(execution_id, {
        "user_request": "test request",
        "result": "test result",
        "__operational__": {"signals": ["START"], "nodes": {}}
    })

    get_context = create_soe_get_context_tool(backends, execution_id)

    result = get_context()

    # Should return all non-operational fields
    assert "user_request" in result
    assert result["user_request"] == "test request"
    assert "result" in result
    assert result["result"] == "test result"
    # Operational fields should be filtered out
    assert "__operational__" not in result


def test_get_context_single_field():
    """Test getting a single field."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "user_request": "test request",
        "result": "test result",
    })

    get_context = create_soe_get_context_tool(backends, execution_id)

    result = get_context(field="user_request")

    assert result == {"user_request": "test request"}


def test_get_context_multiple_fields():
    """Test getting multiple specific fields."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "field1": "value1",
        "field2": "value2",
        "field3": "value3",
    })

    get_context = create_soe_get_context_tool(backends, execution_id)

    result = get_context(fields=["field1", "field3"])

    assert result == {"field1": "value1", "field3": "value3"}


def test_get_context_missing_field():
    """Test getting a field that doesn't exist."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "existing": "value",
    })

    get_context = create_soe_get_context_tool(backends, execution_id)

    result = get_context(field="nonexistent")

    assert result == {"nonexistent": None}


def test_get_context_empty():
    """Test getting context when empty."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {})

    get_context = create_soe_get_context_tool(backends, execution_id)

    result = get_context()

    assert result == {}
