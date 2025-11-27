"""
Tests for Appendix B: Jinja Usage in SOE

These tests verify the Jinja patterns documented in appendix_b_jinja.md.
Each test demonstrates a specific Jinja usage pattern through the public interface.

Test Categories:
1. Prompt rendering with context
2. Context-based conditions (Router, LLM, Agent)
3. Tool conditions (result-based)
4. LLM signal selection (LLM decides - no Jinja)
5. Operational context access
"""

import pytest
from soe import orchestrate
from tests.test_cases.lib import (
    create_test_backends,
    create_nodes,
    extract_signals,
    create_call_llm,
)


# =============================================================================
# WORKFLOWS
# =============================================================================

# 1. Prompt rendering
workflow_prompt_rendering = """
jinja_prompt_workflow:
  RenderPrompt:
    node_type: llm
    event_triggers: [START]
    prompt: |
      Hello {{ context.user_name }}, you requested info about {{ context.topic }}.
    output_field: response
    event_emissions:
      - signal_name: DONE
"""

# 2. Router conditions (context-based) - conditions must be mutually exclusive
workflow_router_conditions = """
router_jinja_workflow:
  CheckAmount:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - condition: "{{ context.amount > 100 }}"
        signal_name: HIGH_VALUE
      - condition: "{{ context.amount > 0 and context.amount <= 100 }}"
        signal_name: LOW_VALUE
      - condition: "{{ context.amount <= 0 }}"
        signal_name: INVALID
"""

# 3. Tool conditions (result-based)
workflow_tool_conditions = """
tool_jinja_workflow:
  ExecuteTool:
    node_type: tool
    event_triggers: [START]
    tool_name: status_checker
    context_parameter_field: check_params
    output_field: check_result
    event_emissions:
      - condition: "{{ result.status == 'ok' }}"
        signal_name: SUCCESS
      - condition: "{{ result.status == 'error' }}"
        signal_name: FAILED
"""

# 4. LLM with Jinja conditions (context-based, not LLM selection)
# Conditions must be mutually exclusive - all matching conditions emit
workflow_llm_jinja_conditions = """
llm_jinja_workflow:
  Generate:
    node_type: llm
    event_triggers: [START]
    prompt: "Generate a response for {{ context.input }}"
    output_field: response
    event_emissions:
      - condition: "{{ context.user_tier == 'premium' }}"
        signal_name: PREMIUM_RESPONSE
      - condition: "{{ context.user_tier != 'premium' }}"
        signal_name: STANDARD_RESPONSE
"""

# 5. Operational context access - conditions must be mutually exclusive
workflow_operational_access = """
operational_workflow:
  FirstNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: FIRST_DONE

  SecondNode:
    node_type: router
    event_triggers: [FIRST_DONE]
    event_emissions:
      - condition: "{{ 'FIRST_DONE' in context.__operational__.signals }}"
        signal_name: SAW_FIRST_SIGNAL
      - condition: "{{ 'FIRST_DONE' not in context.__operational__.signals }}"
        signal_name: DID_NOT_SEE
"""

# 6. Missing context variables (graceful handling)
workflow_missing_context = """
missing_context_workflow:
  RenderWithMissing:
    node_type: llm
    event_triggers: [START]
    prompt: "Hello {{ context.name }}, your order {{ context.order_id }} is ready."
    output_field: response
    event_emissions:
      - signal_name: DONE
"""


# =============================================================================
# TEST HELPERS
# =============================================================================


def status_checker(status: str) -> dict:
    """Tool that returns a status object based on status param."""
    return {"status": status, "checked": True}


# =============================================================================
# TESTS: Prompt Rendering
# =============================================================================

def test_prompt_renders_context_variables():
    """
    Jinja templates in prompts render context variables.

    Pattern: {{ context.field_name }} in prompt
    """
    backends = create_test_backends("jinja_prompt")

    # Track what prompt was sent
    received_prompts = []

    def tracking_llm(prompt: str, config: dict) -> str:
        received_prompts.append(prompt)
        return '{"response": "ok"}'

    call_llm = create_call_llm(stub=tracking_llm)
    nodes, broadcast = create_nodes(backends, call_llm=call_llm)

    execution_id = orchestrate(
        config=workflow_prompt_rendering,
        initial_workflow_name="jinja_prompt_workflow",
        initial_signals=["START"],
        initial_context={"user_name": "Alice", "topic": "testing"},
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    # Verify prompt was rendered with context values
    assert len(received_prompts) == 1
    assert "Alice" in received_prompts[0]
    assert "testing" in received_prompts[0]

    backends.cleanup_all()


# =============================================================================
# TESTS: Context-Based Conditions (Router)
# =============================================================================

def test_router_condition_high_value():
    """
    Context-based conditions evaluate against context.
    Router, LLM, and Agent nodes all support this pattern.

    Pattern: condition: "{{ context.field > value }}"
    """
    backends = create_test_backends("router_high")
    nodes, broadcast = create_nodes(backends)

    execution_id = orchestrate(
        config=workflow_router_conditions,
        initial_workflow_name="router_jinja_workflow",
        initial_signals=["START"],
        initial_context={"amount": 150},  # > 100
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "HIGH_VALUE" in signals
    assert "LOW_VALUE" not in signals
    assert "INVALID" not in signals

    backends.cleanup_all()


def test_router_condition_low_value():
    """
    Router conditions match in order, first truthy wins.
    """
    backends = create_test_backends("router_low")
    nodes, broadcast = create_nodes(backends)

    execution_id = orchestrate(
        config=workflow_router_conditions,
        initial_workflow_name="router_jinja_workflow",
        initial_signals=["START"],
        initial_context={"amount": 50},  # > 0 but <= 100
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "LOW_VALUE" in signals
    assert "HIGH_VALUE" not in signals

    backends.cleanup_all()


def test_router_fallback_signal():
    """
    Condition for amount <= 0 emits INVALID signal.
    All matching conditions emit - conditions must be mutually exclusive.
    """
    backends = create_test_backends("router_fallback")
    nodes, broadcast = create_nodes(backends)

    execution_id = orchestrate(
        config=workflow_router_conditions,
        initial_workflow_name="router_jinja_workflow",
        initial_signals=["START"],
        initial_context={"amount": -10},  # <= 0
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "INVALID" in signals
    assert "HIGH_VALUE" not in signals
    assert "LOW_VALUE" not in signals

    backends.cleanup_all()


# =============================================================================
# TESTS: Tool Conditions (Result-Based)
# =============================================================================

def test_tool_condition_evaluates_result_not_context():
    """
    Tool conditions evaluate against result, not context.

    Pattern: condition: "{{ result.field == value }}"
    """
    backends = create_test_backends("tool_result")

    tools_registry = {
        "status_checker": status_checker
    }

    nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=workflow_tool_conditions,
        initial_workflow_name="tool_jinja_workflow",
        initial_signals=["START"],
        initial_context={"check_params": {"status": "ok"}},
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "SUCCESS" in signals
    assert "FAILED" not in signals

    backends.cleanup_all()


def test_tool_condition_failure_case():
    """
    Tool conditions match the actual result status.
    """
    backends = create_test_backends("tool_failure")

    tools_registry = {
        "status_checker": status_checker
    }

    nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=workflow_tool_conditions,
        initial_workflow_name="tool_jinja_workflow",
        initial_signals=["START"],
        initial_context={"check_params": {"status": "error"}},
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "FAILED" in signals
    assert "SUCCESS" not in signals

    backends.cleanup_all()


# =============================================================================
# TESTS: Context-Based Conditions (LLM)
# =============================================================================

def test_llm_jinja_condition_premium_user():
    """
    LLM nodes with Jinja conditions evaluate against context.
    Same pattern as router - SOE evaluates, not LLM.

    This is different from LLM signal selection (where LLM decides).
    Here, SOE evaluates the condition based on input context.
    """
    backends = create_test_backends("llm_jinja_premium")

    def stub_llm(prompt: str, config: dict) -> str:
        return '{"response": "Generated response"}'

    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast = create_nodes(backends, call_llm=call_llm)

    execution_id = orchestrate(
        config=workflow_llm_jinja_conditions,
        initial_workflow_name="llm_jinja_workflow",
        initial_signals=["START"],
        initial_context={"input": "test", "user_tier": "premium"},
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "PREMIUM_RESPONSE" in signals
    assert "STANDARD_RESPONSE" not in signals

    backends.cleanup_all()


def test_llm_jinja_condition_standard_user():
    """
    Non-premium users get the fallback signal.
    """
    backends = create_test_backends("llm_jinja_standard")

    def stub_llm(prompt: str, config: dict) -> str:
        return '{"response": "Generated response"}'

    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast = create_nodes(backends, call_llm=call_llm)

    execution_id = orchestrate(
        config=workflow_llm_jinja_conditions,
        initial_workflow_name="llm_jinja_workflow",
        initial_signals=["START"],
        initial_context={"input": "test", "user_tier": "free"},
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    assert "STANDARD_RESPONSE" in signals
    assert "PREMIUM_RESPONSE" not in signals

    backends.cleanup_all()


# =============================================================================
# TESTS: Operational Context Access
# =============================================================================

def test_operational_context_accessible_in_jinja():
    """
    The __operational__ namespace is accessible in Jinja conditions.

    Pattern: {{ context.__operational__.signals }}
    """
    backends = create_test_backends("operational_access")
    nodes, broadcast = create_nodes(backends)

    execution_id = orchestrate(
        config=workflow_operational_access,
        initial_workflow_name="operational_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    signals = extract_signals(backends, execution_id)

    # Second node should see FIRST_DONE in operational signals
    assert "SAW_FIRST_SIGNAL" in signals
    assert "DID_NOT_SEE" not in signals

    backends.cleanup_all()


# =============================================================================
# TESTS: Missing Context Variables
# =============================================================================

def test_missing_context_renders_as_empty():
    """
    Missing context variables render as empty strings, not errors.

    This allows progressive context building where not all fields
    are available at every step.
    """
    backends = create_test_backends("missing_context")

    received_prompts = []

    def tracking_llm(prompt: str, config: dict) -> str:
        received_prompts.append(prompt)
        return '{"response": "ok"}'

    call_llm = create_call_llm(stub=tracking_llm)
    nodes, broadcast = create_nodes(backends, call_llm=call_llm)

    execution_id = orchestrate(
        config=workflow_missing_context,
        initial_workflow_name="missing_context_workflow",
        initial_signals=["START"],
        initial_context={"name": "Alice"},  # order_id is missing
        backends=backends,
        broadcast_signals_caller=broadcast,
    )

    # Should complete without error
    signals = extract_signals(backends, execution_id)
    assert "DONE" in signals

    # Prompt should have Alice but empty for order_id
    assert "Alice" in received_prompts[0]

    backends.cleanup_all()
