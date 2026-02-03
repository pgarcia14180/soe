"""
Guide Chapter 4: Tool Nodes - Edge Cases

This test suite covers edge cases and failure modes for Tool nodes:
- Missing tool in registry
- Missing parameters in context
- Invalid parameter types
- Tools without event_emissions
- Condition evaluation errors
- Inline parameters (new feature)
"""

import pytest
from soe import orchestrate
from soe.types import WorkflowValidationError
from tests.test_cases.lib import create_test_backends, create_tool_nodes, extract_signals

# --- Workflows ---

workflow_simple_tool = """
example_workflow:
  ExecuteTool:
    node_type: tool
    event_triggers: [START]
    tool_name: my_tool
    context_parameter_field: params
    output_field: result
    event_emissions:
      - signal_name: SUCCESS
"""

workflow_inline_parameters = """
example_workflow:
  ExecuteToolInline:
    node_type: tool
    event_triggers: [START]
    tool_name: my_tool
    parameters:
      name: "hardcoded_name"
      count: 42
    output_field: result
    event_emissions:
      - signal_name: SUCCESS
"""

workflow_inline_parameters_with_jinja = """
example_workflow:
  ExecuteToolInlineJinja:
    node_type: tool
    event_triggers: [START]
    tool_name: my_tool
    parameters:
      name: "{{ context.user_name }}"
      count: 10
    output_field: result
    event_emissions:
      - signal_name: SUCCESS
"""

workflow_tool_no_emissions = """
example_workflow:
  ExecuteToolNoEmissions:
    node_type: tool
    event_triggers: [START]
    tool_name: my_tool
    context_parameter_field: params
    output_field: result
"""

workflow_tool_bad_condition = """
example_workflow:
  ExecuteToolBadCondition:
    node_type: tool
    event_triggers: [START]
    tool_name: my_tool
    context_parameter_field: params
    output_field: result
    event_emissions:
      - signal_name: SUCCESS
        condition: "{{ result.nonexistent.deeply.nested }}"
"""

# --- Tools ---

def my_tool(name: str, count: int) -> dict:
    """A simple tool that requires name and count."""
    return {"processed": name, "count": count}


# --- Tests ---

def test_missing_tool_in_registry():
    """
    If the tool_name is not in the registry, validation should fail.
    """
    backends = create_test_backends("tool_missing")

    # Empty registry - tool not found
    tools_registry = {}

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    with pytest.raises(WorkflowValidationError) as excinfo:
        orchestrate(
            config=workflow_simple_tool,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"params": {"name": "test", "count": 5}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

    assert "my_tool" in str(excinfo.value)
    assert "not found" in str(excinfo.value)

    backends.cleanup_all()


def test_missing_context_parameter():
    """
    If the context_parameter_field is missing from context,
    the tool emits a failure signal via registry's failure_signal.
    """
    backends = create_test_backends("tool_missing_param")

    tools_registry = {
        "my_tool": {
            "function": my_tool,
            "failure_signal": "FAILURE",
        }
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=workflow_simple_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},  # Missing "params" field
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # Should emit failure signal
    assert "FAILURE" in signals
    assert "SUCCESS" not in signals

    backends.cleanup_all()


def test_tool_exception_emits_failure():
    """
    If the tool function raises an exception,
    the error is caught and registry's failure_signal is emitted.
    """
    def failing_tool(name: str, count: int) -> dict:
        raise RuntimeError("Tool crashed!")

    backends = create_test_backends("tool_exception")

    tools_registry = {
        "my_tool": {
            "function": failing_tool,
            "failure_signal": "FAILURE",
        }
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=workflow_simple_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"params": {"name": "test", "count": 5}},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Should emit failure signal
    assert "FAILURE" in signals
    assert "SUCCESS" not in signals

    # Error message stored in output_field
    assert "Tool crashed!" in context["result"]

    backends.cleanup_all()


def test_tool_without_event_emissions():
    """
    A tool node with no event_emissions should execute successfully
    but emit no signals.
    This exercises the empty event_emissions check in evaluate_tool_conditions.
    """
    def my_tool(name: str, count: int) -> dict:
        return {"processed": name, "count": count}

    backends = create_test_backends("tool_no_emissions")

    tools_registry = {
        "my_tool": {
            "function": my_tool,
        }
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=workflow_tool_no_emissions,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"params": {"name": "test", "count": 5}},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool executed, result stored
    assert "result" in context
    # Only START signal (no event_emissions configured)
    assert "SUCCESS" not in signals

    backends.cleanup_all()


def test_tool_condition_evaluation_error():
    """
    If a condition evaluation fails (e.g., accessing non-existent nested field),
    the error should be logged and no signals emitted for that emission.
    The tool should NOT crash.
    """
    def my_tool(name: str, count: int) -> dict:
        # Return a simple result without nested structure
        return {"processed": name}

    backends = create_test_backends("tool_bad_condition")

    tools_registry = {
        "my_tool": {
            "function": my_tool,
        }
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=workflow_tool_bad_condition,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"params": {"name": "test", "count": 5}},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool executed, result stored
    assert "result" in context
    # Condition failed silently - no SUCCESS signal
    assert "SUCCESS" not in signals

    backends.cleanup_all()


# --- Inline Parameters Tests ---

def test_inline_parameters():
    """
    Tool nodes can specify parameters directly in YAML instead of from context.
    The 'parameters' field provides inline kwargs to the tool function.
    """
    def my_tool(name: str, count: int) -> dict:
        return {"processed": name, "count": count}

    backends = create_test_backends("tool_inline_params")

    tools_registry = {
        "my_tool": my_tool,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=workflow_inline_parameters,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},  # No context params needed - using inline
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool executed with inline parameters
    assert context["result"][-1]["processed"] == "hardcoded_name"
    assert context["result"][-1]["count"] == 42
    assert "SUCCESS" in signals

    backends.cleanup_all()


def test_inline_parameters_with_jinja():
    """
    Inline parameters support Jinja templates to reference context values.
    This enables dynamic parameters with static structure.
    """
    def my_tool(name: str, count: int) -> dict:
        return {"processed": name, "count": count}

    backends = create_test_backends("tool_inline_params_jinja")

    tools_registry = {
        "my_tool": my_tool,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=workflow_inline_parameters_with_jinja,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"user_name": "Alice"},  # Jinja will reference this
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool executed with Jinja-rendered parameters
    assert context["result"][-1]["processed"] == "Alice"
    assert context["result"][-1]["count"] == 10
    assert "SUCCESS" in signals

    backends.cleanup_all()
