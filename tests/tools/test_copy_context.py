"""
Tests for copy_context builtin tool.
"""

import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_copy_context import create_soe_copy_context_tool


def test_copy_context_single_field():
    """Test copying a single field within the same execution."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup source context
    backends.context.save_context(execution_id, {
        "source_field": "test_value",
        "other_field": "other_value",
    })

    copy_context = create_soe_copy_context_tool(backends, execution_id)

    result = copy_context(fields={"source_field": "target_field"})

    assert result["status"] == "copied"
    assert result["fields_copied"] == {"source_field": "target_field"}

    # Verify context was updated
    context = backends.context.get_context(execution_id)
    assert context["target_field"] == "test_value"
    assert context["source_field"] == "test_value"  # Original still there


def test_copy_context_all_fields():
    """Test copying all fields."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "field1": "value1",
        "field2": "value2",
        "__operational__": {"signals": []},
    })

    copy_context = create_soe_copy_context_tool(backends, execution_id)

    result = copy_context(all_fields=True, target_execution_id="target_exec")

    assert result["status"] == "copied"
    assert result["target_execution"] == "target_exec"
    assert "field1" in result["fields_copied"]
    assert "field2" in result["fields_copied"]
    assert "__operational__" not in result["fields_copied"]  # Operational filtered out

    # Verify target context
    target_context = backends.context.get_context("target_exec")
    assert target_context["field1"] == "value1"
    assert target_context["field2"] == "value2"
    assert "__operational__" not in target_context


def test_copy_context_missing_source_field():
    """Test copying a field that doesn't exist."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "existing": "value",
    })

    copy_context = create_soe_copy_context_tool(backends, execution_id)

    result = copy_context(fields={"nonexistent": "target"})

    assert "error" in result
    assert "not found" in result["error"]


def test_copy_context_no_parameters():
    """Test calling without required parameters."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    copy_context = create_soe_copy_context_tool(backends, execution_id)

    result = copy_context()

    assert "error" in result
    assert "Must specify" in result["error"]
