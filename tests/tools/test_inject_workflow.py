import pytest
import json
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_inject_workflow import create_soe_inject_workflow_tool
from soe.types import WorkflowValidationError

def test_soe_inject_workflow_json():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    workflow_name = "test_workflow"
    workflow_data = {
        "node1": {
            "node_type": "llm",
            "prompt": "Hello {{ context.name }}",
            "event_triggers": ["START"]
        }
    }

    # Setup: Initialize operational context for telemetry AND empty workflow registry
    backends.workflow.save_workflows_registry(execution_id, {})
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })

    result = inject_tool(workflow_name, json.dumps(workflow_data))

    assert result["injected"] is True
    assert result["workflow_name"] == workflow_name

    registry = backends.workflow.soe_get_workflows_registry(execution_id)
    assert workflow_name in registry
    assert registry[workflow_name] == workflow_data

    # Assert Telemetry
    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_inject_workflow"
    assert events[0]["context"]["workflow_name"] == workflow_name

def test_soe_inject_workflow_yaml():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    workflow_name = "test_workflow_yaml"
    workflow_yaml = """
    node1:
      node_type: llm
      prompt: "Hello {{ context.name }}"
      event_triggers: ["START"]
    """

    # Setup: Initialize operational context for telemetry AND empty workflow registry
    backends.workflow.save_workflows_registry(execution_id, {})
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })

    result = inject_tool(workflow_name, workflow_yaml)

    assert result["injected"] is True

    registry = backends.workflow.soe_get_workflows_registry(execution_id)
    assert workflow_name in registry
    assert registry[workflow_name]["node1"]["node_type"] == "llm"

    # Assert Telemetry
    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_inject_workflow"
    assert events[0]["context"]["workflow_name"] == workflow_name

def test_soe_inject_workflow_invalid_data():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Workflow data must be a dictionary"):
        inject_tool("test", "invalid json")

def test_soe_inject_workflow_validation_error():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    # Missing node_type
    invalid_workflow = {
        "node1": {
            "config": {}
        }
    }

    with pytest.raises(WorkflowValidationError): # Validation error from validate_workflow
        inject_tool("test", json.dumps(invalid_workflow))


def test_soe_inject_workflow_single_workflow_container():
    """
    Test injecting a workflow where the YAML/JSON has a single non-node entry.
    This exercises the 'single workflow container' branch.
    """
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    # Workflow wrapped in a single container key (not the target name)
    workflow_data = {
        "my_internal_workflow": {
            "node1": {
                "node_type": "llm",
                "prompt": "Hello",
                "event_triggers": ["START"]
            }
        }
    }

    backends.workflow.save_workflows_registry(execution_id, {})
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })

    # Inject with a different name than what's in the container
    result = inject_tool("target_workflow", json.dumps(workflow_data))

    assert result["injected"] is True
    registry = backends.workflow.soe_get_workflows_registry(execution_id)
    assert "target_workflow" in registry
    # Should have extracted the inner workflow
    assert "node1" in registry["target_workflow"]


def test_soe_inject_workflow_multiple_non_node_entries():
    """
    Test injecting a workflow where the structure has multiple non-node entries.
    This exercises the 'multiple entries' branch where entire structure is used.
    """
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    # Multiple entries that don't all have node_type
    workflow_data = {
        "metadata": {"version": "1.0"},  # Not a node
        "config": {"debug": True},  # Not a node
    }

    backends.workflow.save_workflows_registry(execution_id, {})
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })

    # This should fail validation since it's not a valid workflow
    with pytest.raises(WorkflowValidationError):
        inject_tool("test_workflow", json.dumps(workflow_data))


def test_soe_inject_workflow_empty_workflow():
    """Test that empty workflow raises ValueError."""
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    inject_tool = create_soe_inject_workflow_tool(execution_id, backends)

    with pytest.raises(ValueError, match="No workflow definition found"):
        inject_tool("test", "{}")
