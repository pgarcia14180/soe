import pytest
from soe.local_backends import create_in_memory_backends
from soe.validation.operational import validate_operational, validate_backends, OperationalValidationError

class TestOperationalSabotage:
    """
    Sabotage tests for operational validation.
    Intentionally corrupts runtime state to verify defensive checks.
    """

    def test_missing_context(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        # Do not initialize context

        with pytest.raises(OperationalValidationError, match="No context found"):
            validate_operational(execution_id, backends)

    def test_missing_operational_key(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        backends.context.save_context(execution_id, {"some_data": 123})
        # Missing __operational__

        with pytest.raises(OperationalValidationError, match="Missing '__operational__'"):
            validate_operational(execution_id, backends)

    def test_missing_required_fields(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        # Missing 'signals', 'nodes', and 'tool_calls'
        backends.context.save_context(execution_id, {
            "__operational__": {
                "llm_calls": 0,
                "errors": 0,
                "main_execution_id": "main"
            }
        })

        with pytest.raises(OperationalValidationError, match="Missing fields"):
            validate_operational(execution_id, backends)

    def test_invalid_signals_type(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        backends.context.save_context(execution_id, {
            "__operational__": {
                "signals": "not_a_list", # Sabotage
                "nodes": {},
                "llm_calls": 0,
                "tool_calls": 0,
                "errors": 0,
                "main_execution_id": "main"
            }
        })

        with pytest.raises(OperationalValidationError, match="Invalid '__operational__.signals'"):
            validate_operational(execution_id, backends)

    def test_invalid_nodes_type(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        backends.context.save_context(execution_id, {
            "__operational__": {
                "signals": [],
                "nodes": "not_a_dict", # Sabotage
                "llm_calls": 0,
                "tool_calls": 0,
                "errors": 0,
                "main_execution_id": "main"
            }
        })

        with pytest.raises(OperationalValidationError, match="Invalid '__operational__.nodes'"):
            validate_operational(execution_id, backends)

    def test_invalid_llm_calls_type(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        backends.context.save_context(execution_id, {
            "__operational__": {
                "signals": [],
                "nodes": {},
                "llm_calls": "not_an_int", # Sabotage
                "tool_calls": 0,
                "errors": 0,
                "main_execution_id": "main"
            }
        })

        with pytest.raises(OperationalValidationError, match="Invalid '__operational__.llm_calls'"):
            validate_operational(execution_id, backends)

    def test_invalid_errors_type(self):
        execution_id = "test_exec_id"
        backends = create_in_memory_backends()
        backends.context.save_context(execution_id, {
            "__operational__": {
                "signals": [],
                "nodes": {},
                "llm_calls": 0,
                "tool_calls": 0,
                "errors": "not_an_int", # Sabotage
                "main_execution_id": "main"
            }
        })

        with pytest.raises(OperationalValidationError, match="Invalid '__operational__.errors'"):
            validate_operational(execution_id, backends)


class TestBackendsValidation:
    """Tests for validate_backends"""

    def test_missing_context_backend(self):
        class MockBackends:
            workflow = "exists"
            # context missing

        with pytest.raises(OperationalValidationError, match="missing required attribute 'context'"):
            validate_backends(MockBackends())

    def test_missing_workflow_backend(self):
        class MockBackends:
            context = "exists"
            # workflow missing

        with pytest.raises(OperationalValidationError, match="missing required attribute 'workflow'"):
            validate_backends(MockBackends())

    def test_none_backend(self):
        class MockBackends:
            context = None # Exists but None
            workflow = "exists"

        with pytest.raises(OperationalValidationError, match="missing required attribute 'context'"):
            validate_backends(MockBackends())
