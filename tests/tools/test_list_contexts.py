"""
Tests for list_contexts builtin tool.
"""

import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_list_contexts import create_soe_list_contexts_tool


def test_list_contexts_current_only():
    """Test listing contexts with only current execution."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {
        "user_request": "test request",
        "__operational__": {"signals": ["START", "DONE"], "nodes": {"Router": 1}}
    })

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    result = list_contexts()

    assert result["current_execution_id"] == execution_id
    # In-memory backend doesn't have storage_dir, so contexts list may be empty
    # This tests the basic structure


def test_list_contexts_exclude_current():
    """Test excluding current execution from list."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {})

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    result = list_contexts(include_current=False)

    assert result["current_execution_id"] == execution_id
    # Current should be excluded from contexts list
    for ctx in result.get("contexts", []):
        assert ctx["execution_id"] != execution_id


def test_list_contexts_structure():
    """Test the structure of returned data."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context.save_context(execution_id, {})

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    result = list_contexts()

    # Check required keys exist
    assert "current_execution_id" in result
    assert "contexts" in result
    assert isinstance(result["contexts"], list)


def test_list_contexts_with_file_backend(tmp_path):
    """Test listing contexts with file-based backend (covers file iteration)."""
    from soe.local_backends import create_local_backends

    execution_id = "current_exec"
    other_id = "other_exec"

    backends = create_local_backends(
        context_storage_dir=str(tmp_path / "contexts"),
        workflow_storage_dir=str(tmp_path / "workflows"),
    )

    # Save multiple contexts to disk
    backends.context.save_context(execution_id, {
        "user_request": ["test request"],
        "__operational__": {
            "signals": ["START", "PROCESS", "DONE"],
            "nodes": {"Router": 1, "Worker": 2}
        }
    })
    backends.context.save_context(other_id, {
        "user_request": ["another request"],
        "__operational__": {
            "signals": ["START"],
            "nodes": {"Entry": 1}
        }
    })

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    result = list_contexts()

    assert result["current_execution_id"] == execution_id
    assert len(result["contexts"]) == 2

    # Find current and other contexts
    current_ctx = next(c for c in result["contexts"] if c["execution_id"] == execution_id)
    other_ctx = next(c for c in result["contexts"] if c["execution_id"] == other_id)

    # Verify current context
    assert current_ctx["is_current"] is True
    assert current_ctx["user_request"] == "test request"
    assert current_ctx["node_count"] == 3  # Router: 1 + Worker: 2
    assert "DONE" in current_ctx["signals"]

    # Verify other context
    assert other_ctx["is_current"] is False
    assert other_ctx["user_request"] == "another request"
    assert other_ctx["node_count"] == 1


def test_list_contexts_exclude_current_file_backend(tmp_path):
    """Test excluding current context with file backend."""
    from soe.local_backends import create_local_backends

    execution_id = "current_exec"
    other_id = "other_exec"

    backends = create_local_backends(
        context_storage_dir=str(tmp_path / "contexts"),
        workflow_storage_dir=str(tmp_path / "workflows"),
    )

    backends.context.save_context(execution_id, {"__operational__": {}})
    backends.context.save_context(other_id, {"__operational__": {}})

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    result = list_contexts(include_current=False)

    assert len(result["contexts"]) == 1
    assert result["contexts"][0]["execution_id"] == other_id


def test_list_contexts_handles_malformed_json(tmp_path):
    """Test graceful handling of corrupted context files."""
    from soe.local_backends import create_local_backends
    import json

    execution_id = "good_exec"

    backends = create_local_backends(
        context_storage_dir=str(tmp_path / "contexts"),
        workflow_storage_dir=str(tmp_path / "workflows"),
    )

    # Save a valid context
    backends.context.save_context(execution_id, {
        "__operational__": {"signals": [], "nodes": {}}
    })

    # Create a malformed JSON file directly
    bad_file = tmp_path / "contexts" / "bad_exec.json"
    bad_file.write_text("{ invalid json }")

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    # Should not crash, just skip the bad file
    result = list_contexts()

    assert result["current_execution_id"] == execution_id
    # Only the valid context should be listed
    assert len(result["contexts"]) == 1
    assert result["contexts"][0]["execution_id"] == execution_id


def test_list_contexts_missing_fields(tmp_path):
    """Test handling contexts with missing optional fields."""
    from soe.local_backends import create_local_backends

    execution_id = "minimal_exec"

    backends = create_local_backends(
        context_storage_dir=str(tmp_path / "contexts"),
        workflow_storage_dir=str(tmp_path / "workflows"),
    )

    # Save context with minimal data (no user_request, no __operational__)
    backends.context.save_context(execution_id, {})

    list_contexts = create_soe_list_contexts_tool(backends, execution_id)

    result = list_contexts()

    assert len(result["contexts"]) == 1
    ctx = result["contexts"][0]
    assert ctx["execution_id"] == execution_id
    assert ctx["user_request"] is None
    assert ctx["signals"] == []
    assert ctx["node_count"] == 0
