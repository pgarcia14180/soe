import pytest
from unittest.mock import MagicMock
from soe.local_backends import create_in_memory_backends
from soe.validation.operational import OperationalValidationError
from soe.nodes.llm.validation.operational import validate_llm_node_runtime
from soe.nodes.agent.validation.operational import validate_agent_node_runtime
from soe.nodes.child.validation.operational import validate_child_node_runtime
from soe.nodes.router.validation.operational import validate_router_node_runtime

class TestNodeOperationalSabotage:
    """
    Sabotage tests for node-specific operational validation.
    """

    def _setup_valid_backends(self, execution_id="test_exec_id"):
        backends = create_in_memory_backends()
        backends.context.save_context(execution_id, {
            "__operational__": {
                "signals": [],
                "nodes": {},
                "llm_calls": 0,
                "tool_calls": 0,
                "errors": 0,
                "main_execution_id": "main"
            }
        })
        backends.workflow.save_workflows_registry(execution_id, {"wf": {}})
        backends.workflow.save_current_workflow_name(execution_id, "wf")
        return backends

    def test_llm_backend_failure(self):
        execution_id = "test_exec_id"
        backends = self._setup_valid_backends(execution_id)

        # Sabotage: Make get_current_workflow_name raise exception
        backends.workflow.get_current_workflow_name = MagicMock(side_effect=Exception("DB Error"))

        with pytest.raises(OperationalValidationError, match="Cannot access workflow backend"):
            validate_llm_node_runtime(execution_id, backends)

    def test_agent_backend_failure(self):
        execution_id = "test_exec_id"
        backends = self._setup_valid_backends(execution_id)

        # Sabotage: Make soe_get_workflows_registry raise exception
        backends.workflow.soe_get_workflows_registry = MagicMock(side_effect=Exception("DB Error"))

        with pytest.raises(OperationalValidationError, match="Cannot access workflow backend"):
            validate_agent_node_runtime(execution_id, backends)

    def test_child_backend_failure(self):
        execution_id = "test_exec_id"
        backends = self._setup_valid_backends(execution_id)

        # Sabotage: Make soe_get_workflows_registry raise exception
        backends.workflow.soe_get_workflows_registry = MagicMock(side_effect=Exception("DB Error"))

        with pytest.raises(OperationalValidationError, match="Cannot access workflow backend"):
            validate_child_node_runtime(execution_id, backends)

    def test_child_empty_registry(self):
        execution_id = "test_exec_id"
        backends = self._setup_valid_backends(execution_id)

        # Sabotage: Empty registry
        backends.workflow.save_workflows_registry(execution_id, {})

        with pytest.raises(OperationalValidationError, match="No workflows_registry found"):
            validate_child_node_runtime(execution_id, backends)

    def test_router_valid_runtime(self):
        """Test router runtime validation (just calls shared validation)."""
        execution_id = "test_exec_id"
        backends = self._setup_valid_backends(execution_id)

        # Should succeed without error
        context = validate_router_node_runtime(execution_id, backends)
        assert "__operational__" in context

    def test_router_sabotage_missing_context(self):
        """Test router runtime validation fails with missing context."""
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        # Do not initialize context

        with pytest.raises(OperationalValidationError, match="No context found"):
            validate_router_node_runtime(execution_id, backends)
