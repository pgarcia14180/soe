import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_get_workflows import create_soe_get_workflows_tool

def test_soe_get_workflows_empty():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Initialize empty registry
    backends.workflow.save_workflows_registry(execution_id, {})

    get_tool = create_soe_get_workflows_tool(execution_id, backends)

    workflows = get_tool()
    assert workflows == {}

def test_soe_get_workflows_populated():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    # Setup: Inject some workflows directly
    workflows_data = {
        "workflow_1": {
            "node1": {"node_type": "TypeA"}
        },
        "workflow_2": {
            "node2": {"node_type": "TypeB"}
        }
    }
    backends.workflow.save_workflows_registry(execution_id, workflows_data)

    get_tool = create_soe_get_workflows_tool(execution_id, backends)

    workflows = get_tool()
    assert len(workflows) == 2
    assert "workflow_1" in workflows
    assert "workflow_2" in workflows
    assert workflows["workflow_1"]["node1"]["node_type"] == "TypeA"
