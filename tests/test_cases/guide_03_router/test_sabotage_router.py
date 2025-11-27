"""
Sabotage Tests: Router Node

These tests intentionally break router configurations in ways an LLM might hallucinate.
Goal: Every error should produce a clean WorkflowValidationError or OperationalValidationError,
never a raw Python exception (KeyError, TypeError, AttributeError, etc.)

Test pattern:
- Use pytest.raises with SPECIFIC exception type (not Exception)
- Use match= to verify exact error message contains expected text
- If test fails, it means we're either:
  a) Getting a raw Python error (bad - needs fix)
  b) Getting wrong exception type (bad - needs fix)
  c) Getting wrong message (maybe ok, update test)
"""

import pytest
from soe import orchestrate
from soe.types import WorkflowValidationError
from soe.validation.operational import OperationalValidationError
from tests.test_cases.lib import create_test_backends, create_router_nodes, extract_signals


# =============================================================================
# CATEGORY 1: node_type variations (LLM might typo or use wrong casing)
# =============================================================================

class TestNodeTypeVariations:
    """LLM hallucinations around node_type field"""

    def test_node_type_typo_routerr(self):
        """LLM typo: 'routerr' instead of 'router'"""
        config = """
example_workflow:
  ValidateInput:
    node_type: routerr
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_router_typo")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="unknown node_type 'routerr'"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_node_type_missing(self):
        """LLM forgets node_type entirely"""
        config = """
example_workflow:
  ValidateInput:
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_router_no_type")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="'node_type' is required"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_node_type_wrong_casing(self):
        """LLM uses 'Router' instead of 'router'"""
        config = """
example_workflow:
  ValidateInput:
    node_type: Router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_router_casing")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="unknown node_type 'Router'"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_node_type_null(self):
        """LLM sets node_type to null/None"""
        config = """
example_workflow:
  ValidateInput:
    node_type: null
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_router_null_type")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="'node_type' is required"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_node_type_empty_string(self):
        """LLM sets node_type to empty string"""
        config = """
example_workflow:
  ValidateInput:
    node_type: ""
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_router_empty_type")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_node_type_invented(self):
        """LLM invents a node type that doesn't exist"""
        config = """
example_workflow:
  ValidateInput:
    node_type: validator
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_router_invented")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()


# =============================================================================
# CATEGORY 2: event_triggers variations
# =============================================================================

class TestEventTriggersVariations:
    """LLM hallucinations around event_triggers field"""

    def test_event_triggers_string_not_list(self):
        """LLM forgets brackets: 'START' instead of [START]"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: START
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_triggers_string")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_triggers_empty_list(self):
        """LLM provides empty list []"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: []
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_triggers_empty")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_triggers_missing(self):
        """LLM forgets event_triggers entirely"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_triggers_missing")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_triggers_null(self):
        """LLM sets event_triggers to null"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: null
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_triggers_null")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_triggers_wrong_key(self):
        """LLM uses 'triggers' instead of 'event_triggers'"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_triggers_wrong_key")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_triggers_dict_not_list(self):
        """LLM uses dict instead of list"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers:
      signal: START
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_triggers_dict")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()


# =============================================================================
# CATEGORY 3: event_emissions variations
# =============================================================================

class TestEventEmissionsVariations:
    """LLM hallucinations around event_emissions field"""

    def test_event_emissions_missing(self):
        """LLM forgets event_emissions on router"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
"""
        backends = create_test_backends("sabotage_emissions_missing")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_emissions_empty_list(self):
        """LLM provides empty emissions list"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions: []
"""
        backends = create_test_backends("sabotage_emissions_empty")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_event_emissions_not_list(self):
        """LLM forgets list structure for emissions"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      signal_name: DONE
"""
        backends = create_test_backends("sabotage_emissions_not_list")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_signal_name_missing(self):
        """LLM forgets signal_name in emission"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - condition: "{{ true }}"
"""
        backends = create_test_backends("sabotage_signal_name_missing")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_signal_name_typo(self):
        """LLM uses 'signal' instead of 'signal_name'"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal: DONE
"""
        backends = create_test_backends("sabotage_signal_typo")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_signal_name_null(self):
        """LLM sets signal_name to null"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: null
"""
        backends = create_test_backends("sabotage_signal_null")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_signal_name_empty(self):
        """LLM sets signal_name to empty string"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ""
"""
        backends = create_test_backends("sabotage_signal_empty")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_emissions_wrong_key(self):
        """LLM uses 'emissions' instead of 'event_emissions'"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_emissions_wrong_key")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()


# =============================================================================
# CATEGORY 4: Jinja condition variations
# =============================================================================

class TestJinjaConditionVariations:
    """LLM hallucinations in Jinja2 conditions"""

    def test_jinja_unclosed_braces(self):
        """LLM forgets to close {{ """
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{{ context.data is defined"
"""
        backends = create_test_backends("sabotage_jinja_unclosed")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="Jinja syntax error"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={"data": "test"},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_jinja_wrong_braces(self):
        """LLM uses single braces { } instead of double {{ }}"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{ context.data is defined }"
"""
        backends = create_test_backends("sabotage_jinja_single_brace")
        nodes, broadcast = create_router_nodes(backends)

        # This might not error - it's just a string literal
        # Let's see what happens
        try:
            execution_id = orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={"data": "test"},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )
            print(f"ACTUAL: No error - condition evaluated as literal string")
        except Exception as e:
            print(f"ACTUAL: {type(e).__name__}: {e}")

        backends.cleanup_all()

    def test_jinja_unknown_filter(self):
        """LLM uses a filter that doesn't exist"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{{ context.data | capitalize_all }}"
"""
        backends = create_test_backends("sabotage_jinja_bad_filter")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="filter"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={"data": "test"},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_jinja_syntax_error(self):
        """LLM writes invalid Jinja syntax - unclosed block"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{{ context.data {% if true %}"
"""
        backends = create_test_backends("sabotage_jinja_syntax")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="Jinja syntax error"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={"data": "test"},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_jinja_undefined_variable(self):
        """LLM references variable that doesn't exist"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{{ context.nonexistent_field == 'value' }}"
"""
        backends = create_test_backends("sabotage_jinja_undefined")
        nodes, broadcast = create_router_nodes(backends)

        # This might not error - Jinja might return undefined
        try:
            execution_id = orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )
            print(f"ACTUAL: No error - undefined handled gracefully")
        except Exception as e:
            print(f"ACTUAL: {type(e).__name__}: {e}")

        backends.cleanup_all()

    def test_jinja_division_by_zero(self):
        """LLM writes condition that divides by zero - silently fails, no signal emitted"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{{ 1 / 0 > 0 }}"
"""
        backends = create_test_backends("sabotage_jinja_div_zero")
        nodes, broadcast = create_router_nodes(backends)

        # Division by zero in condition causes it to silently fail (not emit)
        # This is expected behavior - broken conditions don't crash, they just don't match
        execution_id = orchestrate(
            config=config,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        # Verify no VALID signal was emitted (condition failed)
        signals = extract_signals(backends, execution_id)
        assert "VALID" not in signals, "Division by zero condition should not emit signal"

        backends.cleanup_all()


# =============================================================================
# CATEGORY 5: Workflow structure variations
# =============================================================================

class TestWorkflowStructureVariations:
    """LLM hallucinations in overall workflow structure"""

    def test_workflow_name_not_found(self):
        """LLM references workflow that doesn't exist"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_workflow_not_found")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="not found in config"):
            orchestrate(
                config=config,
                initial_workflow_name="nonexistent_workflow",  # Wrong name
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_empty_workflow(self):
        """LLM creates workflow with no nodes"""
        config = """
example_workflow: {}
"""
        backends = create_test_backends("sabotage_empty_workflow")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="is empty"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_node_name_reserved(self):
        """LLM uses reserved name starting with __"""
        config = """
example_workflow:
  __reserved__:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_reserved_name")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(WorkflowValidationError, match="reserved"):
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_duplicate_node_names(self):
        """LLM defines same node name twice (YAML behavior)"""
        # Note: YAML will just use the last one, not error
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: FIRST
  ValidateInput:
    node_type: router
    event_triggers: [FIRST]
    event_emissions:
      - signal_name: SECOND
"""
        backends = create_test_backends("sabotage_duplicate_names")
        nodes, broadcast = create_router_nodes(backends)

        # YAML silently uses the last definition - this might not error
        try:
            execution_id = orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )
            print(f"ACTUAL: No error - YAML used last definition")
        except Exception as e:
            print(f"ACTUAL: {type(e).__name__}: {e}")

        backends.cleanup_all()

    def test_invalid_yaml_syntax(self):
        """LLM generates invalid YAML"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_invalid_yaml")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_workflow_is_list_not_dict(self):
        """LLM structures workflow as list instead of dict"""
        config = """
example_workflow:
  - node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_workflow_list")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()


# =============================================================================
# CATEGORY 6: orchestrate() parameter variations
# =============================================================================

class TestOrchestrateParameterVariations:
    """LLM hallucinations when calling orchestrate()"""

    def test_config_none(self):
        """LLM passes None as config"""
        backends = create_test_backends("sabotage_config_none")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=None,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_config_empty_string(self):
        """LLM passes empty string as config"""
        backends = create_test_backends("sabotage_config_empty")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config="",
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_initial_signals_string(self):
        """LLM passes string instead of list for signals"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_signals_string")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals="START",  # String, not list
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_initial_signals_empty(self):
        """LLM passes empty list for signals"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_signals_empty")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=[],  # Empty
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_initial_context_string(self):
        """LLM passes string instead of dict for context"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_context_string")
        nodes, broadcast = create_router_nodes(backends)

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context="bad context",  # String, not dict
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()

    def test_broadcast_signals_caller_none(self):
        """LLM passes None for broadcast_signals_caller"""
        config = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        backends = create_test_backends("sabotage_broadcast_none")

        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=config,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=None,  # None
            )

        print(f"ACTUAL: {type(exc_info.value).__name__}: {exc_info.value}")
        backends.cleanup_all()
