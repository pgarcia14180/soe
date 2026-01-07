import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_remove_node import create_soe_remove_node_tool


def test_soe_remove_node_success():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup: Create a workflow with multiple nodes
    workflow_name = "test_workflow"
    initial_workflow = {
        "node1": {
            "node_type": "llm",
            "prompt": "Hi",
            "event_triggers": ["START"]
        },
        "node2": {
            "node_type": "router",
            "event_triggers": ["NEXT"]
        }
    }
    backends.workflow.save_workflows_registry(execution_id, {workflow_name: initial_workflow})

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

    remove_tool = create_soe_remove_node_tool(execution_id, backends)

    result = remove_tool(workflow_name, "node1")

    assert result["removed"] is True
    assert result["workflow_name"] == workflow_name
    assert result["node_name"] == "node1"

    registry = backends.workflow.get_workflows_registry(execution_id)
    assert "node1" not in registry[workflow_name]
    assert "node2" in registry[workflow_name]  # Other node still exists

    # Assert Telemetry
    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_remove_node"
    assert events[0]["context"]["workflow_name"] == workflow_name
    assert events[0]["context"]["node_name"] == "node1"


def test_soe_remove_node_workflow_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.workflow.save_workflows_registry(execution_id, {})

    remove_tool = create_soe_remove_node_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Workflow 'nonexistent' not found"):
        remove_tool("nonexistent", "node1")


def test_soe_remove_node_node_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    workflow_name = "test_workflow"
    backends.workflow.save_workflows_registry(execution_id, {
        workflow_name: {"node1": {"node_type": "router", "event_triggers": ["START"]}}
    })

    remove_tool = create_soe_remove_node_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Node 'nonexistent' not found in workflow 'test_workflow'"):
        remove_tool(workflow_name, "nonexistent")
