"""
Validation error tests for all node types.

Tests validation logic that raises WorkflowValidationError for invalid configurations.
Happy path (valid configs) is covered by other tests.
"""

import pytest
from soe.types import WorkflowValidationError
from soe.nodes.router.validation import validate_node_config as validate_router
from soe.nodes.tool.validation import validate_node_config as validate_tool
from soe.nodes.child.validation import validate_node_config as validate_child
from soe.nodes.llm.validation import validate_node_config as validate_llm
from soe.nodes.agent.validation import validate_node_config as validate_agent
from soe.lib.yaml_parser import parse_yaml
from soe.validation.config import validate_workflow, validate_config


class TestYamlParsing:
    """YAML parsing error tests"""

    def test_invalid_yaml_syntax(self):
        invalid_yaml = """
        key: value
        broken: [unclosed bracket
        """
        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_yaml(invalid_yaml)


class TestWorkflowValidation:
    """Workflow-level validation errors"""

    def test_unknown_node_type(self):
        """Unknown node_type should fail validation."""
        with pytest.raises(WorkflowValidationError, match="unknown node_type 'quantum'"):
            validate_workflow("test_workflow", {
                "MyNode": {
                    "node_type": "quantum",
                    "event_triggers": ["START"]
                }
            })

    def test_workflow_not_dict(self):
        """Workflow must be a dict, not a list or string."""
        with pytest.raises(WorkflowValidationError, match="must be an object containing node definitions"):
            validate_config({
                "bad_workflow": ["node1", "node2"]
            })

    def test_internal_node_type_skipped(self):
        """Internal node types (starting with _) are skipped during validation."""
        # This should not raise - internal nodes are skipped
        validate_workflow("parent_workflow", {
            "ValidRouter": {
                "node_type": "router",
                "event_triggers": ["START"],
                "event_emissions": [{"signal_name": "DONE"}]
            },
            "_ParentSync": {
                "node_type": "_parent",
                "some_internal_config": True
            }
        })


class TestRouterValidation:
    """Router node validation errors"""

    def test_missing_event_triggers(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_router({})

    def test_event_triggers_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' must be a list"):
            validate_router({"event_triggers": "START"})

    def test_missing_event_emissions(self):
        with pytest.raises(WorkflowValidationError, match="'event_emissions' is required"):
            validate_router({"event_triggers": ["START"]})

    def test_event_emissions_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_emissions' must be a list"):
            validate_router({"event_triggers": ["START"], "event_emissions": "DONE"})

    def test_event_emission_not_dict(self):
        with pytest.raises(WorkflowValidationError, match="must be an object with 'signal_name'"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": ["DONE"]
            })

    def test_event_emission_missing_signal_name(self):
        with pytest.raises(WorkflowValidationError, match="missing 'signal_name'"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{"condition": "true"}]
            })

    def test_event_emission_invalid_condition(self):
        with pytest.raises(WorkflowValidationError, match="invalid 'condition'"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{"signal_name": "DONE", "condition": 123}]
            })


class TestToolValidation:
    """Tool node validation errors"""

    def test_missing_event_triggers(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_tool({})

    def test_event_triggers_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' must be a list"):
            validate_tool({"event_triggers": "RUN"})

    def test_missing_tool_name(self):
        with pytest.raises(WorkflowValidationError, match="'tool_name' is required"):
            validate_tool({"event_triggers": ["RUN"]})

    def test_event_emissions_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_emissions' must be a list"):
            validate_tool({
                "event_triggers": ["RUN"],
                "tool_name": "my_tool",
                "event_emissions": "not_a_list"
            })

    def test_event_emissions_item_not_dict(self):
        with pytest.raises(WorkflowValidationError, match="must be a dict"):
            validate_tool({
                "event_triggers": ["RUN"],
                "tool_name": "my_tool",
                "event_emissions": ["not_a_dict"]
            })

    def test_event_emissions_missing_signal_name(self):
        with pytest.raises(WorkflowValidationError, match="must have 'signal_name'"):
            validate_tool({
                "event_triggers": ["RUN"],
                "tool_name": "my_tool",
                "event_emissions": [{"condition": "true"}]
            })

    def test_output_field_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'output_field' must be a string"):
            validate_tool({
                "event_triggers": ["RUN"],
                "tool_name": "my_tool",
                "output_field": 123
            })

    def test_output_field_reserved(self):
        with pytest.raises(WorkflowValidationError, match="cannot be '__operational__'"):
            validate_tool({
                "event_triggers": ["RUN"],
                "tool_name": "my_tool",
                "output_field": "__operational__"
            })

    def test_tool_not_registered(self):
        """Tool name not in registry and not a builtin tool"""
        from soe.nodes.tool.validation.config import validate_tool_node_config
        with pytest.raises(WorkflowValidationError, match="not found in tools_registry"):
            validate_tool_node_config(
                {"event_triggers": ["RUN"], "tool_name": "nonexistent_tool"},
                tools_registry={}  # empty registry
            )


class TestChildValidation:
    """Child node validation errors"""

    def test_missing_child_workflow_name(self):
        with pytest.raises(WorkflowValidationError, match="'child_workflow_name' is required"):
            validate_child({})

    def test_child_workflow_name_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'child_workflow_name' must be a string"):
            validate_child({"child_workflow_name": 123})

    def test_missing_child_initial_signals(self):
        with pytest.raises(WorkflowValidationError, match="'child_initial_signals' is required"):
            validate_child({"child_workflow_name": "sub"})

    def test_child_initial_signals_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'child_initial_signals' must be a list"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": "START"
            })

    def test_missing_event_triggers(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"]
            })

    def test_event_triggers_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' must be a list"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": "RUN"
            })

    def test_signals_to_parent_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'signals_to_parent' must be a list"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "signals_to_parent": "DONE"
            })

    def test_signals_to_parent_item_not_string(self):
        with pytest.raises(WorkflowValidationError, match="must be strings"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "signals_to_parent": [123]
            })

    def test_context_updates_to_parent_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'context_updates_to_parent' must be a list"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "context_updates_to_parent": "result"
            })

    def test_context_updates_to_parent_item_not_string(self):
        with pytest.raises(WorkflowValidationError, match="must be strings"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "context_updates_to_parent": [123]
            })

    def test_input_fields_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'input_fields' must be a list"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "input_fields": "data"
            })

    def test_fan_out_field_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'fan_out_field' must be a string"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "fan_out_field": 123
            })

    def test_fan_out_field_missing_child_input_field(self):
        with pytest.raises(WorkflowValidationError, match="'child_input_field' is required when 'fan_out_field' is set"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "fan_out_field": "items"
            })

    def test_child_input_field_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'child_input_field' must be a string"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "fan_out_field": "items",
                "child_input_field": 123
            })

    def test_spawn_interval_not_number(self):
        with pytest.raises(WorkflowValidationError, match="'spawn_interval' must be a number"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "spawn_interval": "fast"
            })

    def test_spawn_interval_negative(self):
        with pytest.raises(WorkflowValidationError, match="'spawn_interval' must be non-negative"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "spawn_interval": -1
            })

    def test_event_emissions_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_emissions' must be a list"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "event_emissions": "DONE"
            })

    def test_event_emission_not_dict(self):
        with pytest.raises(WorkflowValidationError, match="must be an object with 'signal_name'"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "event_emissions": ["DONE"]
            })

    def test_event_emission_missing_signal_name(self):
        with pytest.raises(WorkflowValidationError, match="missing 'signal_name'"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "event_emissions": [{"description": "done"}]
            })

    def test_event_emission_invalid_condition(self):
        with pytest.raises(WorkflowValidationError, match="invalid 'condition'"):
            validate_child({
                "child_workflow_name": "sub",
                "child_initial_signals": ["START"],
                "event_triggers": ["RUN"],
                "event_emissions": [{"signal_name": "DONE", "condition": 123}]
            })


class TestLlmValidation:
    """LLM node validation errors"""

    def test_missing_event_triggers(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_llm({})

    def test_event_triggers_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' must be a list"):
            validate_llm({"event_triggers": "START"})

    def test_missing_prompt(self):
        with pytest.raises(WorkflowValidationError, match="'prompt' is required"):
            validate_llm({"event_triggers": ["START"]})

    def test_input_fields_rejected(self):
        with pytest.raises(WorkflowValidationError, match="'input_fields' is no longer supported"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "input_fields": ["data"]
            })

    def test_output_field_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'output_field' must be a string"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "output_field": 123
            })

    def test_output_field_reserved(self):
        with pytest.raises(WorkflowValidationError, match="cannot be '__operational__'"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "output_field": "__operational__"
            })

    def test_retries_not_integer(self):
        with pytest.raises(WorkflowValidationError, match="'retries' must be a positive integer"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "retries": "3"
            })

    def test_retries_negative(self):
        with pytest.raises(WorkflowValidationError, match="'retries' must be a positive integer"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "retries": -1
            })

    def test_event_emissions_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_emissions' must be a list"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "event_emissions": "DONE"
            })

    def test_event_emission_not_dict(self):
        with pytest.raises(WorkflowValidationError, match="must be an object with 'signal_name'"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "event_emissions": ["DONE"]
            })

    def test_event_emission_missing_signal_name(self):
        with pytest.raises(WorkflowValidationError, match="missing 'signal_name'"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "event_emissions": [{"description": "done"}]
            })

    def test_event_emission_invalid_condition(self):
        with pytest.raises(WorkflowValidationError, match="invalid 'condition'"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "event_emissions": [{"signal_name": "DONE", "condition": 123}]
            })

    def test_identity_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'identity' must be a string"):
            validate_llm({
                "event_triggers": ["START"],
                "prompt": "Hello",
                "identity": 123
            })


class TestAgentValidation:
    """Agent node validation errors"""

    def test_missing_event_triggers(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_agent({})

    def test_event_triggers_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_triggers' must be a list"):
            validate_agent({"event_triggers": "START"})

    def test_missing_prompt(self):
        with pytest.raises(WorkflowValidationError, match="'prompt' is required"):
            validate_agent({"event_triggers": ["START"]})

    def test_input_fields_rejected(self):
        with pytest.raises(WorkflowValidationError, match="'input_fields' is no longer supported"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "input_fields": ["data"]
            })

    def test_output_field_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'output_field' must be a string"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "output_field": 123
            })

    def test_output_field_reserved(self):
        with pytest.raises(WorkflowValidationError, match="cannot be '__operational__'"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "output_field": "__operational__"
            })

    def test_retries_not_integer(self):
        with pytest.raises(WorkflowValidationError, match="'retries' must be a positive integer"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "retries": "3"
            })

    def test_retries_negative(self):
        with pytest.raises(WorkflowValidationError, match="'retries' must be a positive integer"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "retries": -1
            })

    def test_event_emissions_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'event_emissions' must be a list"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "event_emissions": "DONE"
            })

    def test_event_emission_not_dict(self):
        with pytest.raises(WorkflowValidationError, match="must be an object with 'signal_name'"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "event_emissions": ["DONE"]
            })

    def test_event_emission_missing_signal_name(self):
        with pytest.raises(WorkflowValidationError, match="missing 'signal_name'"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "event_emissions": [{"description": "done"}]
            })

    def test_event_emission_invalid_condition(self):
        with pytest.raises(WorkflowValidationError, match="invalid 'condition'"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "event_emissions": [{"signal_name": "DONE", "condition": 123}]
            })

    def test_tools_not_list(self):
        with pytest.raises(WorkflowValidationError, match="'tools' must be a list"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "tools": "my_tool"
            })

    def test_identity_not_string(self):
        with pytest.raises(WorkflowValidationError, match="'identity' must be a string"):
            validate_agent({
                "event_triggers": ["START"],
                "prompt": "Do task",
                "identity": 123
            })


# =============================================================================
# Orchestrate Parameter Validation (broker.py)
# =============================================================================

class TestOrchestrateValidation:
    """Validation of orchestrate() parameters."""

    def test_initial_signals_string_not_list(self):
        """initial_signals must be a list, not a string."""
        from soe import orchestrate
        from soe.local_backends import create_in_memory_backends

        backends = create_in_memory_backends()
        config = """
test_workflow:
  Node:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        with pytest.raises(WorkflowValidationError, match="'initial_signals' must be a list"):
            orchestrate(
                config=config,
                initial_workflow_name="test_workflow",
                initial_signals="START",  # String, not list
                initial_context={},
                backends=backends,
                broadcast_signals_caller=lambda id, signals: None,
            )

    def test_initial_signals_empty(self):
        """initial_signals cannot be empty."""
        from soe import orchestrate
        from soe.local_backends import create_in_memory_backends

        backends = create_in_memory_backends()
        config = """
test_workflow:
  Node:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        with pytest.raises(WorkflowValidationError, match="'initial_signals' cannot be empty"):
            orchestrate(
                config=config,
                initial_workflow_name="test_workflow",
                initial_signals=[],  # Empty
                initial_context={},
                backends=backends,
                broadcast_signals_caller=lambda id, signals: None,
            )

    def test_workflow_name_not_in_config(self):
        """initial_workflow_name must exist in config."""
        from soe import orchestrate
        from soe.local_backends import create_in_memory_backends

        backends = create_in_memory_backends()
        config = """
test_workflow:
  Node:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""
        with pytest.raises(WorkflowValidationError, match="not found in config"):
            orchestrate(
                config=config,
                initial_workflow_name="nonexistent_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=lambda id, signals: None,
            )


# =============================================================================
# Workflow Structure Validation
# =============================================================================

class TestWorkflowStructureValidation:
    """Validation of workflow structure."""

    def test_empty_workflow(self):
        """Workflow with no nodes should fail."""
        with pytest.raises(WorkflowValidationError, match="is empty"):
            validate_workflow("empty_workflow", {})

    def test_reserved_node_name(self):
        """Node names starting with __ are reserved."""
        with pytest.raises(WorkflowValidationError, match="reserved"):
            validate_workflow("test_workflow", {
                "__internal__": {
                    "node_type": "router",
                    "event_triggers": ["START"],
                    "event_emissions": [{"signal_name": "DONE"}]
                }
            })


# =============================================================================
# Jinja Syntax Validation
# =============================================================================

class TestJinjaSyntaxValidation:
    """Validation of Jinja syntax in conditions."""

    def test_unclosed_braces(self):
        """Unclosed {{ should fail validation."""
        with pytest.raises(WorkflowValidationError, match="Jinja syntax error"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{
                    "signal_name": "DONE",
                    "condition": "{{ context.data is defined"
                }]
            })

    def test_unknown_filter(self):
        """Unknown Jinja filter should fail validation."""
        with pytest.raises(WorkflowValidationError, match="filter"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{
                    "signal_name": "DONE",
                    "condition": "{{ context.data | nonexistent_filter }}"
                }]
            })

    def test_unclosed_block(self):
        """Unclosed {% if %} should fail validation."""
        with pytest.raises(WorkflowValidationError, match="Jinja syntax error"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{
                    "signal_name": "DONE",
                    "condition": "{% if context.data %}"
                }]
            })


# =============================================================================
# LLM Hallucination Tests - Common typos and mistakes
# =============================================================================

class TestRouterHallucinations:
    """Common LLM hallucinations for router nodes."""

    def test_event_trigger_singular_typo(self):
        """LLM might use 'event_trigger' (singular) instead of 'event_triggers'."""
        # This should fail because event_triggers is required
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_router({
                "event_trigger": ["START"],  # Typo: singular
                "event_emissions": [{"signal_name": "DONE"}]
            })

    def test_triggers_instead_of_event_triggers(self):
        """LLM might use 'triggers' instead of 'event_triggers'."""
        with pytest.raises(WorkflowValidationError, match="'event_triggers' is required"):
            validate_router({
                "triggers": ["START"],  # Wrong name
                "event_emissions": [{"signal_name": "DONE"}]
            })

    def test_emissions_instead_of_event_emissions(self):
        """LLM might use 'emissions' instead of 'event_emissions'."""
        with pytest.raises(WorkflowValidationError, match="'event_emissions' is required"):
            validate_router({
                "event_triggers": ["START"],
                "emissions": [{"signal_name": "DONE"}]  # Wrong name
            })

    def test_emit_instead_of_signal_name(self):
        """LLM might use 'emit' instead of 'signal_name' in emission."""
        with pytest.raises(WorkflowValidationError, match="missing 'signal_name'"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{"emit": "DONE"}]  # Wrong name
            })

    def test_signal_instead_of_signal_name(self):
        """LLM might use 'signal' instead of 'signal_name' in emission."""
        with pytest.raises(WorkflowValidationError, match="missing 'signal_name'"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": [{"signal": "DONE"}]  # Wrong name
            })


class TestLlmHallucinations:
    """Common LLM hallucinations for llm nodes."""

    def test_message_instead_of_prompt(self):
        """LLM might use 'message' instead of 'prompt'."""
        with pytest.raises(WorkflowValidationError, match="'prompt' is required"):
            validate_llm({
                "event_triggers": ["START"],
                "message": "Hello"  # Wrong name
            })

    def test_system_prompt_instead_of_prompt(self):
        """LLM might use 'system_prompt' instead of 'prompt'."""
        with pytest.raises(WorkflowValidationError, match="'prompt' is required"):
            validate_llm({
                "event_triggers": ["START"],
                "system_prompt": "You are helpful"  # Wrong name
            })

    def test_text_instead_of_prompt(self):
        """LLM might use 'text' instead of 'prompt'."""
        with pytest.raises(WorkflowValidationError, match="'prompt' is required"):
            validate_llm({
                "event_triggers": ["START"],
                "text": "Hello"  # Wrong name
            })


class TestToolHallucinations:
    """Common LLM hallucinations for tool nodes."""

    def test_name_instead_of_tool_name(self):
        """LLM might use 'name' instead of 'tool_name'."""
        with pytest.raises(WorkflowValidationError, match="'tool_name' is required"):
            validate_tool({
                "event_triggers": ["START"],
                "name": "my_tool"  # Wrong name
            })

    def test_function_instead_of_tool_name(self):
        """LLM might use 'function' instead of 'tool_name'."""
        with pytest.raises(WorkflowValidationError, match="'tool_name' is required"):
            validate_tool({
                "event_triggers": ["START"],
                "function": "my_tool"  # Wrong name
            })

    def test_tool_instead_of_tool_name(self):
        """LLM might use 'tool' instead of 'tool_name'."""
        with pytest.raises(WorkflowValidationError, match="'tool_name' is required"):
            validate_tool({
                "event_triggers": ["START"],
                "tool": "my_tool"  # Wrong name
            })


class TestChildHallucinations:
    """Common LLM hallucinations for child nodes."""

    def test_workflow_name_instead_of_child_workflow_name(self):
        """LLM might use 'workflow_name' instead of 'child_workflow_name'."""
        with pytest.raises(WorkflowValidationError, match="'child_workflow_name' is required"):
            validate_child({
                "event_triggers": ["START"],
                "workflow_name": "sub",  # Wrong name
                "child_initial_signals": ["START"]
            })

    def test_child_workflow_instead_of_child_workflow_name(self):
        """LLM might use 'child_workflow' instead of 'child_workflow_name'."""
        with pytest.raises(WorkflowValidationError, match="'child_workflow_name' is required"):
            validate_child({
                "event_triggers": ["START"],
                "child_workflow": "sub",  # Wrong name
                "child_initial_signals": ["START"]
            })

    def test_initial_signals_instead_of_child_initial_signals(self):
        """LLM might use 'initial_signals' instead of 'child_initial_signals'."""
        with pytest.raises(WorkflowValidationError, match="'child_initial_signals' is required"):
            validate_child({
                "event_triggers": ["START"],
                "child_workflow_name": "sub",
                "initial_signals": ["START"]  # Wrong name
            })

    def test_start_signals_instead_of_child_initial_signals(self):
        """LLM might use 'start_signals' instead of 'child_initial_signals'."""
        with pytest.raises(WorkflowValidationError, match="'child_initial_signals' is required"):
            validate_child({
                "event_triggers": ["START"],
                "child_workflow_name": "sub",
                "start_signals": ["START"]  # Wrong name
            })


class TestAgentHallucinations:
    """Common LLM hallucinations for agent nodes."""

    def test_tool_names_instead_of_tools(self):
        """LLM might use 'tool_names' instead of 'tools'."""
        # Agent with 'tools' is optional, so this should pass validation
        # but the wrong field is just ignored - valid but unexpected
        # This test documents the expected behavior
        validate_agent({
            "event_triggers": ["START"],
            "prompt": "Do task",
            "tool_names": ["my_tool"]  # Wrong name - ignored silently
        })
        # No error - but tools won't be available!

    def test_available_tools_instead_of_tools(self):
        """LLM might use 'available_tools' instead of 'tools'."""
        validate_agent({
            "event_triggers": ["START"],
            "prompt": "Do task",
            "available_tools": ["my_tool"]  # Wrong name - ignored silently
        })
        # No error - but tools won't be available!


class TestWorkflowStructureHallucinations:
    """Common LLM hallucinations in workflow structure."""

    def test_type_instead_of_node_type(self):
        """LLM might use 'type' instead of 'node_type'."""
        with pytest.raises(WorkflowValidationError, match="'node_type' is required"):
            validate_workflow("test", {
                "MyNode": {
                    "type": "router",  # Wrong name
                    "event_triggers": ["START"],
                    "event_emissions": [{"signal_name": "DONE"}]
                }
            })

    def test_nodeType_camelcase(self):
        """LLM might use 'nodeType' (camelCase) instead of 'node_type'."""
        with pytest.raises(WorkflowValidationError, match="'node_type' is required"):
            validate_workflow("test", {
                "MyNode": {
                    "nodeType": "router",  # camelCase
                    "event_triggers": ["START"],
                    "event_emissions": [{"signal_name": "DONE"}]
                }
            })

    def test_workflow_as_list_not_dict(self):
        """LLM might define workflow as a list of nodes instead of dict."""
        with pytest.raises(WorkflowValidationError, match="must be an object"):
            validate_config({
                "test_workflow": [
                    {"name": "MyNode", "node_type": "router"}  # List, not dict
                ]
            })


class TestCombinedConfigValidation:
    """Test validation of combined config format (workflows + context_schema + identities)."""

    def test_context_schema_not_dict(self):
        """context_schema section must be a dict."""
        with pytest.raises(WorkflowValidationError, match="'context_schema' section must be an object"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyRouter": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "context_schema": ["field1", "field2"]  # Should be dict, not list
            })

    def test_context_schema_field_invalid_type(self):
        """context_schema field schema must be dict or string."""
        with pytest.raises(WorkflowValidationError, match="schema must be an object or type string"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyRouter": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "context_schema": {
                    "valid_field": "string",
                    "invalid_field": 12345  # Should be dict or string, not int
                }
            })

    def test_identities_not_dict(self):
        """identities section must be a dict."""
        with pytest.raises(WorkflowValidationError, match="'identities' section must be an object"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyRouter": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "identities": ["identity1", "identity2"]  # Should be dict, not list
            })

    def test_identity_prompt_not_string(self):
        """Identity prompt must be a string."""
        with pytest.raises(WorkflowValidationError, match="identity prompt must be a string"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyRouter": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "identities": {
                    "valid_identity": "You are a helpful assistant.",
                    "invalid_identity": {"prompt": "nested dict"}  # Should be string, not dict
                }
            })

    def test_workflows_section_not_dict(self):
        """workflows section in combined config must be a dict."""
        with pytest.raises(WorkflowValidationError, match="'workflows' section must be an object"):
            validate_config({
                "workflows": "not a dict",
                "identities": {"assistant": "You are helpful."}
            })

    def test_workflow_in_workflows_section_not_dict(self):
        """Each workflow in workflows section must be a dict."""
        with pytest.raises(WorkflowValidationError, match="must be an object containing node definitions"):
            validate_config({
                "workflows": {
                    "valid_workflow": {
                        "MyRouter": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    },
                    "invalid_workflow": "not a dict"
                }
            })



class TestCombinedConfigValidation:
    """Validation for combined config format (workflows + context_schema + identities)."""

    def test_context_schema_not_dict(self):
        """context_schema section must be a dict."""
        with pytest.raises(WorkflowValidationError, match="'context_schema' section must be an object"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyNode": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "context_schema": ["field1", "field2"]  # List, not dict
            })

    def test_context_schema_field_invalid_type(self):
        """context_schema field schema must be dict or string."""
        with pytest.raises(WorkflowValidationError, match="context_schema.bad_field: schema must be"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyNode": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "context_schema": {
                    "good_field": {"type": "string"},
                    "bad_field": 12345  # Number, not dict or string
                }
            })

    def test_identities_not_dict(self):
        """identities section must be a dict."""
        with pytest.raises(WorkflowValidationError, match="'identities' section must be an object"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyNode": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "identities": ["identity1", "identity2"]  # List, not dict
            })

    def test_identity_prompt_not_string(self):
        """identity prompt must be a string."""
        with pytest.raises(WorkflowValidationError, match="identities.bad_identity: identity prompt must be a string"):
            validate_config({
                "workflows": {
                    "test": {
                        "MyNode": {
                            "node_type": "router",
                            "event_triggers": ["START"],
                            "event_emissions": [{"signal_name": "DONE"}]
                        }
                    }
                },
                "identities": {
                    "good_identity": "You are a helpful assistant",
                    "bad_identity": {"prompt": "nested dict"}  # Dict, not string
                }
            })

    def test_workflows_section_not_dict(self):
        """workflows section must be a dict."""
        with pytest.raises(WorkflowValidationError, match="'workflows' section must be an object"):
            validate_config({
                "workflows": "not a dict",
                "identities": {"assistant": "You are helpful"}
            })
