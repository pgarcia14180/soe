"""
Tests for update_context builtin tool.
"""

import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_update_context import create_soe_update_context_tool


def test_update_context_single_field():
    """Test updating a single field."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "existing": "old_value",
    })

    update_context = create_soe_update_context_tool(backends, execution_id)

    result = update_context(updates={"new_field": "new_value"})

    assert result["status"] == "updated"
    assert "new_field" in result["fields"]

    # Verify context was actually updated
    context = backends.context.get_context(execution_id)
    assert context["new_field"] == "new_value"
    assert context["existing"] == "old_value"


def test_update_context_multiple_fields():
    """Test updating multiple fields."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {})

    update_context = create_soe_update_context_tool(backends, execution_id)

    result = update_context(updates={
        "field1": "value1",
        "field2": "value2",
        "field3": 123
    })

    assert result["status"] == "updated"
    assert set(result["fields"]) == {"field1", "field2", "field3"}

    context = backends.context.get_context(execution_id)
    assert context["field1"] == "value1"
    assert context["field2"] == "value2"
    assert context["field3"] == 123


def test_update_context_overwrites_existing():
    """Test that updates overwrite existing fields."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "field": "old_value",
    })

    update_context = create_soe_update_context_tool(backends, execution_id)

    result = update_context(updates={"field": "new_value"})

    assert result["status"] == "updated"

    context = backends.context.get_context(execution_id)
    assert context["field"] == "new_value"


def test_update_context_blocks_operational_fields():
    """Test that operational fields cannot be updated."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "__operational__": {"signals": ["START"]},
    })

    update_context = create_soe_update_context_tool(backends, execution_id)

    result = update_context(updates={"__operational__": {"hacked": True}})

    assert result["status"] == "no valid updates (operational fields cannot be updated)"

    # Verify operational was not changed
    context = backends.context.get_context(execution_id)
    assert context["__operational__"]["signals"] == ["START"]
    assert "hacked" not in context["__operational__"]


def test_update_context_empty_updates():
    """Test with empty updates dict."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {})

    update_context = create_soe_update_context_tool(backends, execution_id)

    result = update_context(updates={})

    assert result["status"] == "no updates provided"


def test_update_context_mixed_valid_and_operational():
    """Test with mix of valid and operational fields."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {})

    update_context = create_soe_update_context_tool(backends, execution_id)

    result = update_context(updates={
        "valid_field": "value",
        "__internal__": "blocked",
    })

    assert result["status"] == "updated"
    assert result["fields"] == ["valid_field"]

    context = backends.context.get_context(execution_id)
    assert context["valid_field"] == "value"
    assert "__internal__" not in context
