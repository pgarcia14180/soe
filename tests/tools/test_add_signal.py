"""
Tests for add_signal builtin tool.

This tool adds signals to a node's event_emissions at runtime.
"""

import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_add_signal import create_soe_add_signal_tool


def _create_backends_with_workflow():
    """Create backends with a pre-registered workflow."""
    backends = create_in_memory_backends()
    execution_id = "test_exec"

    # Register a workflow
    workflows = {
        "example_workflow": {
            "ProcessNode": {
                "node_type": "router",
                "event_triggers": ["START"],
                "event_emissions": [
                    {"signal_name": "EXISTING_SIGNAL"}
                ]
            },
            "EmptyNode": {
                "node_type": "router",
                "event_triggers": ["TRIGGER"],
                "event_emissions": []
            }
        }
    }
    backends.workflow.save_workflows_registry(execution_id, workflows)

    # Initialize operational context (required for register_event)
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })

    return backends, execution_id


def test_add_signal_new_signal():
    """Test adding a new signal to a node."""
    backends, execution_id = _create_backends_with_workflow()

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    result = add_signal(
        workflow_name="example_workflow",
        node_name="ProcessNode",
        signal_name="NEW_SIGNAL",
        condition="{{ context.ready }}"
    )

    assert result["status"] == "added"
    assert "NEW_SIGNAL" in result["message"]

    # Verify the signal was added
    workflows = backends.workflow.soe_get_workflows_registry(execution_id)
    node = workflows["example_workflow"]["ProcessNode"]
    signals = [e["signal_name"] for e in node["event_emissions"]]
    assert "NEW_SIGNAL" in signals
    assert "EXISTING_SIGNAL" in signals  # Original still there


def test_add_signal_update_existing():
    """Test updating an existing signal's condition."""
    backends, execution_id = _create_backends_with_workflow()

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    result = add_signal(
        workflow_name="example_workflow",
        node_name="ProcessNode",
        signal_name="EXISTING_SIGNAL",
        condition="{{ context.new_condition }}"
    )

    assert result["status"] == "updated"
    assert "EXISTING_SIGNAL" in result["message"]

    # Verify the condition was updated
    workflows = backends.workflow.soe_get_workflows_registry(execution_id)
    node = workflows["example_workflow"]["ProcessNode"]
    existing = next(e for e in node["event_emissions"] if e["signal_name"] == "EXISTING_SIGNAL")
    assert existing["condition"] == "{{ context.new_condition }}"


def test_add_signal_to_empty_emissions():
    """Test adding signal to node with empty event_emissions."""
    backends, execution_id = _create_backends_with_workflow()

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    result = add_signal(
        workflow_name="example_workflow",
        node_name="EmptyNode",
        signal_name="FIRST_SIGNAL",
        condition="{{ true }}"
    )

    assert result["status"] == "added"

    # Verify the signal was added
    workflows = backends.workflow.soe_get_workflows_registry(execution_id)
    node = workflows["example_workflow"]["EmptyNode"]
    assert len(node["event_emissions"]) == 1
    assert node["event_emissions"][0]["signal_name"] == "FIRST_SIGNAL"


def test_add_signal_to_node_without_emissions():
    """Test adding signal to node that has no event_emissions key."""
    backends, execution_id = _create_backends_with_workflow()

    # Add a node without event_emissions
    workflows = backends.workflow.soe_get_workflows_registry(execution_id)
    workflows["example_workflow"]["NoEmissionsNode"] = {
        "node_type": "router",
        "event_triggers": ["SOMETHING"]
    }
    backends.workflow.save_workflows_registry(execution_id, workflows)

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    result = add_signal(
        workflow_name="example_workflow",
        node_name="NoEmissionsNode",
        signal_name="ADDED_SIGNAL",
        condition="{{ context.flag }}"
    )

    assert result["status"] == "added"

    # Verify event_emissions was created
    workflows = backends.workflow.soe_get_workflows_registry(execution_id)
    node = workflows["example_workflow"]["NoEmissionsNode"]
    assert "event_emissions" in node
    assert node["event_emissions"][0]["signal_name"] == "ADDED_SIGNAL"


def test_add_signal_workflow_not_found():
    """Test error when workflow doesn't exist."""
    backends, execution_id = _create_backends_with_workflow()

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    with pytest.raises(ValueError, match="not found"):
        add_signal(
            workflow_name="nonexistent_workflow",
            node_name="SomeNode",
            signal_name="SIGNAL",
            condition="{{ true }}"
        )


def test_add_signal_node_not_found():
    """Test error when node doesn't exist in workflow."""
    backends, execution_id = _create_backends_with_workflow()

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    with pytest.raises(ValueError, match="not found"):
        add_signal(
            workflow_name="example_workflow",
            node_name="nonexistent_node",
            signal_name="SIGNAL",
            condition="{{ true }}"
        )


def test_add_signal_registers_telemetry_event():
    """Test that adding a signal registers a telemetry event."""
    backends, execution_id = _create_backends_with_workflow()

    add_signal = create_soe_add_signal_tool(execution_id, backends)

    add_signal(
        workflow_name="example_workflow",
        node_name="ProcessNode",
        signal_name="TELEMETRY_TEST",
        condition="{{ true }}"
    )

    # Check telemetry was recorded
    events = backends.telemetry.get_events(execution_id)
    add_signal_events = [e for e in events if e.get("context", {}).get("tool") == "add_signal"]
    assert len(add_signal_events) == 1
    assert add_signal_events[0]["context"]["signal"] == "TELEMETRY_TEST"
