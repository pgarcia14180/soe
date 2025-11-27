import pytest
import json
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_inject_node import create_soe_inject_node_tool

def test_inject_node_config_json():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup: Create a workflow to modify
    workflow_name = "test_workflow"
    initial_workflow = {
        "node1": {
            "node_type": "llm",
            "prompt": "Hi",
            "event_triggers": ["START"]
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

    inject_tool = create_soe_inject_node_tool(execution_id, backends)

    node_name = "node2"
    node_config = {
        "node_type": "tool",
        "tool": "search",
        "event_triggers": ["PROCESS"]
    }

    result = inject_tool(workflow_name, node_name, json.dumps(node_config))

    assert result["injected"] is True
    assert result["workflow_name"] == workflow_name
    assert result["node_name"] == node_name

    registry = backends.workflow.soe_get_workflows_registry(execution_id)
    assert node_name in registry[workflow_name]
    assert registry[workflow_name][node_name] == node_config

    # Assert Telemetry
    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_inject_node"
    assert events[0]["context"]["workflow_name"] == workflow_name
    assert events[0]["context"]["node_name"] == node_name

def test_inject_node_config_yaml():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup: Create a workflow to modify
    workflow_name = "test_workflow"
    initial_workflow = {}
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

    inject_tool = create_soe_inject_node_tool(execution_id, backends)

    node_name = "node1"
    node_config_yaml = """
    node_type: llm
    prompt: "Hello"
    event_triggers: ["START"]
    """

    result = inject_tool(workflow_name, node_name, node_config_yaml)

    assert result["injected"] is True

    registry = backends.workflow.soe_get_workflows_registry(execution_id)
    assert registry[workflow_name][node_name]["node_type"] == "llm"

    # Assert Telemetry
    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_inject_node"
    assert events[0]["context"]["workflow_name"] == workflow_name
    assert events[0]["context"]["node_name"] == node_name

def test_inject_node_config_missing_workflow():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Initialize empty registry
    backends.workflow.save_workflows_registry(execution_id, {})

    inject_tool = create_soe_inject_node_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Workflow 'missing_workflow' not found"):
        inject_tool("missing_workflow", "node1", "{}")

def test_inject_node_config_invalid_data():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup
    workflow_name = "test_workflow"
    backends.workflow.save_workflows_registry(execution_id, {workflow_name: {}})

    inject_tool = create_soe_inject_node_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Node configuration must be a dictionary"):
        inject_tool(workflow_name, "node1", "invalid json")
