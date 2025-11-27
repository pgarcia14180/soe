import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_remove_workflow import create_soe_remove_workflow_tool


def test_soe_remove_workflow_success():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup: Create a workflow to remove
    workflow_name = "test_workflow"
    initial_workflow = {
        "node1": {
            "node_type": "llm",
            "prompt": "Hi",
            "event_triggers": ["START"]
        }
    }
    backends.workflow.save_workflows_registry(execution_id, {
        workflow_name: initial_workflow,
        "other_workflow": {"node2": {"node_type": "router", "event_triggers": ["START"]}}
    })

    # Setup: Initialize operational context for telemetry
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })

    remove_tool = create_soe_remove_workflow_tool(execution_id, backends)

    result = remove_tool(workflow_name)

    assert result["removed"] is True
    assert result["workflow_name"] == workflow_name

    registry = backends.workflow.soe_get_workflows_registry(execution_id)
    assert workflow_name not in registry
    assert "other_workflow" in registry  # Other workflow still exists

    # Assert Telemetry
    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_remove_workflow"
    assert events[0]["context"]["workflow_name"] == workflow_name


def test_soe_remove_workflow_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.workflow.save_workflows_registry(execution_id, {})

    remove_tool = create_soe_remove_workflow_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Workflow 'nonexistent' not found"):
        remove_tool("nonexistent")
