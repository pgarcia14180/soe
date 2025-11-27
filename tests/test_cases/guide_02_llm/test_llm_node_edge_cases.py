"""
Guide Chapter 2: LLM Nodes - Edge Cases

This test suite covers edge cases and failure modes for LLM nodes:
- Missing context variables in prompts
- LLM validation failures (invalid JSON)
- Retry logic
- Invalid signal selection
"""

import os
import pytest
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_llm_nodes, extract_signals, create_call_llm


def is_integration_mode():
    return os.environ.get("SOE_INTEGRATION") == "1"


# --- Workflows for Edge Cases ---

# 1. Missing Context Variable
workflow_missing_context = """
example_workflow:
  NodeMissingContext:
    node_type: llm
    event_triggers: [START]
    prompt: "Process this: {{ context.missing_var }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""

# 2. Validation Failure (Invalid JSON)
workflow_validation_failure = """
example_workflow:
  NodeValidationFail:
    node_type: llm
    event_triggers: [START]
    prompt: "Return a result"
    output_field: result
    retries: 2
    event_emissions:
      - signal_name: DONE
"""

# 3. Invalid Signal Selection
workflow_signal_selection_fail = """
example_workflow:
  NodeSignalFail:
    node_type: llm
    event_triggers: [START]
    prompt: "Pick a signal"
    output_field: analysis
    retries: 1
    event_emissions:
      - signal_name: OPTION_A
        condition: "Option A"
      - signal_name: OPTION_B
        condition: "Option B"
"""

# 4. LLM Failure with Signal Emission
workflow_llm_failure_signal = """
example_workflow:
  NodeWithFailureSignal:
    node_type: llm
    event_triggers: [START]
    prompt: "Return a result"
    output_field: result
    retries: 1
    llm_failure_signal: LLM_FAILED
    event_emissions:
      - signal_name: DONE
"""


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_missing_context_variable():
    """
    If a context variable is missing in the Jinja template, it renders as empty string.
    The node should NOT crash, but proceed with the empty value.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # The variable {{ context.missing_var }} should be empty
        return '{"result": "processed"}'

    backends = create_test_backends("llm_missing_context")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_missing_context,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"other_var": "exists"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # The key test: node did NOT crash, result field exists
    assert "result" in context
    # Signal was emitted (workflow completed)
    assert "DONE" in signals

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Tests deliberate bad responses - not meaningful with real LLM"
)
def test_llm_validation_retry_failure():
    """
    If LLM returns invalid JSON (doesn't match output_field),
    it should retry 'retries' times and then raise an exception.
    """
    call_count = {"n": 0}

    def stub_llm(prompt: str, config: dict) -> str:
        call_count["n"] += 1
        # Return invalid JSON (missing the 'result' field or malformed)
        return '{"wrong_field": "value"}'

    backends = create_test_backends("llm_validation_fail")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    # Expect the orchestration to fail with an exception after retries
    with pytest.raises(Exception) as excinfo:
        orchestrate(
            config=workflow_validation_failure,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

    # Check that it retried (initial + 2 retries = 3 calls)
    # Note: The implementation loop is `range(max_retries + 1)`, so 0, 1, 2 = 3 attempts.
    assert call_count["n"] == 3
    assert "Max retries" in str(excinfo.value)

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Tests deliberate bad responses - not meaningful with real LLM"
)
def test_llm_signal_selection_failure():
    """
    If LLM selects a signal that is not in the allowed list,
    it should be treated as a validation error and retry.
    """
    call_count = {"n": 0}

    def stub_llm(prompt: str, config: dict) -> str:
        call_count["n"] += 1
        # Return a signal that is not OPTION_A or OPTION_B
        return '{"analysis": "test", "selected_signal": "INVALID_OPTION"}'

    backends = create_test_backends("llm_signal_fail")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    with pytest.raises(Exception) as excinfo:
        orchestrate(
            config=workflow_signal_selection_fail,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

    # Retries: 1 retry configured -> 2 attempts total
    assert call_count["n"] == 2
    assert "Max retries" in str(excinfo.value)

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Tests deliberate bad responses - not meaningful with real LLM"
)
def test_llm_validation_recovery():
    """
    Test that the node can recover if the LLM fixes its output on a retry.
    """
    call_count = {"n": 0}

    def stub_llm(prompt: str, config: dict) -> str:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return '{"wrong_field": "oops"}'  # Fail first attempt
        else:
            return '{"result": "success"}'    # Succeed second attempt

    backends = create_test_backends("llm_recovery")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_validation_failure, # Uses retries: 2
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    assert context["result"][-1] == "success"
    assert call_count["n"] == 2  # Should have taken 2 attempts

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Tests deliberate bad responses - not meaningful with real LLM"
)
def test_llm_failure_emits_signal():
    """
    When llm_failure_signal is configured and LLM fails after retries,
    the node emits the failure signal instead of raising an exception.
    """
    call_count = {"n": 0}

    def stub_llm(prompt: str, config: dict) -> str:
        call_count["n"] += 1
        # Always return invalid JSON
        return '{"wrong_field": "value"}'

    backends = create_test_backends("llm_failure_signal")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    # Should NOT raise - emits failure signal instead
    execution_id = orchestrate(
        config=workflow_llm_failure_signal,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # Failure signal emitted, not DONE
    assert "LLM_FAILED" in signals
    assert "DONE" not in signals
    # Retried: 1 retry configured -> 2 attempts total
    assert call_count["n"] == 2

    backends.cleanup_all()


# --- Jinja Edge Cases ---

# Context field is None
workflow_none_context = """
example_workflow:
  NodeNoneContext:
    node_type: llm
    event_triggers: [START]
    prompt: "Value is: {{ context.nullable_field }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""

# Context field is empty string
workflow_empty_string_context = """
example_workflow:
  NodeEmptyString:
    node_type: llm
    event_triggers: [START]
    prompt: "Value is: {{ context.empty_field }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""

# Bracket syntax for context variable
workflow_bracket_syntax = """
example_workflow:
  NodeBracketSyntax:
    node_type: llm
    event_triggers: [START]
    prompt: "Value is: {{ context['bracket_var'] }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""

# Jinja syntax error in prompt
workflow_jinja_syntax_error = """
example_workflow:
  NodeSyntaxError:
    node_type: llm
    event_triggers: [START]
    prompt: "Broken template: {{ context.field"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_context_field_is_none():
    """
    If a context field value is explicitly None, it should render as empty.
    The node should NOT crash.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        return '{"result": "processed"}'

    backends = create_test_backends("llm_none_context")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_none_context,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"nullable_field": None},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_context_field_is_empty_string():
    """
    If a context field value is an empty string, it should render as empty.
    The node should NOT crash.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        return '{"result": "processed"}'

    backends = create_test_backends("llm_empty_string")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_empty_string_context,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"empty_field": ""},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_bracket_syntax_variable():
    """
    Context variables accessed with bracket syntax should work.
    E.g., {{ context['my_var'] }}
    """
    def stub_llm(prompt: str, config: dict) -> str:
        assert "hello" in prompt  # Variable was resolved
        return '{"result": "processed"}'

    backends = create_test_backends("llm_bracket_syntax")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_bracket_syntax,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"bracket_var": "hello"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_jinja_syntax_error_in_prompt():
    """
    If a Jinja template has a syntax error, the prompt should be returned as-is
    and the LLM should still be called (with the broken template as prompt).
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # The broken template is passed as-is
        assert "{{ context.field" in prompt
        return '{"result": "processed"}'

    backends = create_test_backends("llm_jinja_error")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_jinja_syntax_error,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"field": "value"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    backends.cleanup_all()


# --- Accumulated Filter and No-Jinja Edge Cases ---

workflow_accumulated_filter = """
example_workflow:
  NodeWithAccumulated:
    node_type: llm
    event_triggers: [START]
    prompt: "Items: {{ context.items | accumulated | join(', ') }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""

workflow_no_jinja_markers = """
example_workflow:
  PlainPrompt:
    node_type: llm
    event_triggers: [START]
    prompt: "This is a plain prompt with no Jinja markers at all"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_accumulated_filter_with_history():
    """
    The accumulated filter should return the full history list for a field.
    This exercises the accumulated_filter function in jinja_render.py.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # Verify accumulated filter returned all items
        assert "apple" in prompt and "banana" in prompt and "cherry" in prompt
        return '{"result": "processed"}'

    backends = create_test_backends("llm_accumulated")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    # Pre-populate context with history (multiple values for same field)
    execution_id = orchestrate(
        config=workflow_accumulated_filter,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"items": ["apple", "banana", "cherry"]},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Jinja edge case test - not meaningful with real LLM"
)
def test_no_jinja_markers_in_prompt():
    """
    If a prompt has no Jinja markers ({{ or {%), it should be passed as-is.
    This exercises the early return path in render_prompt.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # The prompt is wrapped in system instructions, but our plain text should be there unmodified
        assert "This is a plain prompt with no Jinja markers at all" in prompt
        return '{"result": "processed"}'

    backends = create_test_backends("llm_no_jinja")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_no_jinja_markers,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    backends.cleanup_all()


# 6. Condition on Output (Self-Reference)
workflow_condition_on_output = """
example_workflow:
  NodeConditionOnOutput:
    node_type: llm
    event_triggers: [START]
    prompt: "Return a status"
    output_field: status
    event_emissions:
      - signal_name: SUCCESS_SIGNAL
        condition: "{{ 'SUCCESS' in context.status }}"
      - signal_name: FAILURE_SIGNAL
        condition: "{{ 'FAILURE' in context.status }}"
"""


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Stub test for condition logic"
)
def test_condition_on_output_field():
    """
    Test that event_emissions conditions can reference the output_field
    that was JUST generated by the node in the current execution.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        return '{"status": "Operation was a SUCCESS"}'

    backends = create_test_backends("llm_condition_output")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=workflow_condition_on_output,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # The condition {{ 'SUCCESS' in context.status }} should evaluate to True
    # because context.status should contain the output we just generated.
    assert "SUCCESS_SIGNAL" in signals
    assert "FAILURE_SIGNAL" not in signals

    backends.cleanup_all()
