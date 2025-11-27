"""
Guide Chapter 1: Basics - Router Edge Cases

Exhaustive edge case tests for the Router node concepts:
- event_triggers: What signals activate the node?
- event_emissions: What signals are produced?
- condition: Jinja2 expressions that control emission

These tests verify behavior at the boundaries of the introduced concepts.
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_router_nodes, extract_signals
from tests.test_cases.workflows.guide_router import (
    router_multiple_triggers,
    router_no_matching_trigger,
    router_multiple_true_conditions,
    router_no_conditions_match,
    router_undefined_variable,
    router_chain,
    router_complex_condition,
    router_boolean_context,
    router_null_handling,
)


# ============================================================================
# event_triggers EDGE CASES
# ============================================================================


def test_router_multiple_triggers_with_start():
    """
    Router with multiple triggers responds to START signal
    """
    backends = create_test_backends("edge_multi_trigger_start")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_multiple_triggers,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "PROCESSED" in signals

    backends.cleanup_all()


def test_router_multiple_triggers_with_retry():
    """
    Router with multiple triggers responds to RETRY signal
    """
    backends = create_test_backends("edge_multi_trigger_retry")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_multiple_triggers,
        initial_workflow_name="example_workflow",
        initial_signals=["RETRY"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "PROCESSED" in signals

    backends.cleanup_all()


def test_router_no_matching_trigger():
    """
    Router does NOT execute when triggered signal doesn't match event_triggers
    """
    backends = create_test_backends("edge_no_match_trigger")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_no_matching_trigger,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],  # Node waits for SOMETHING_ELSE
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    # Only START should be in signals, not SHOULD_NOT_EMIT
    assert "SHOULD_NOT_EMIT" not in signals

    backends.cleanup_all()


# ============================================================================
# event_emissions + condition EDGE CASES
# ============================================================================


def test_router_multiple_true_conditions_emits_all():
    """
    When multiple conditions are true, ALL matching signals are emitted
    """
    backends = create_test_backends("edge_multi_true")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_multiple_true_conditions,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"value": 15},  # Both > 5 and > 10 are true
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "FIRST_MATCH" in signals
    assert "SECOND_MATCH" in signals

    backends.cleanup_all()


def test_router_multiple_conditions_only_first_true():
    """
    When only first condition is true, only that signal is emitted
    """
    backends = create_test_backends("edge_only_first_true")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_multiple_true_conditions,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"value": 7},  # > 5 is true, > 10 is false
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "FIRST_MATCH" in signals
    assert "SECOND_MATCH" not in signals

    backends.cleanup_all()


def test_router_no_conditions_match():
    """
    When no conditions are true, no signals are emitted (beyond START)
    """
    backends = create_test_backends("edge_no_match")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_no_conditions_match,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"value": 50},  # Neither > 100 nor < 0
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "HIGH" not in signals
    assert "LOW" not in signals

    backends.cleanup_all()


# ============================================================================
# Jinja2 condition EDGE CASES
# ============================================================================


def test_router_undefined_variable_is_defined_check():
    """
    Jinja2 'is defined' correctly identifies missing variables
    """
    backends = create_test_backends("edge_undefined_var")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_undefined_variable,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},  # missing_field is not defined
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "MISSING" in signals
    assert "EXISTS" not in signals

    backends.cleanup_all()


def test_router_defined_variable():
    """
    Jinja2 'is defined' correctly identifies present variables
    """
    backends = create_test_backends("edge_defined_var")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_undefined_variable,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"missing_field": "actually present"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "EXISTS" in signals
    assert "MISSING" not in signals

    backends.cleanup_all()


def test_router_complex_nested_condition():
    """
    Complex Jinja2 expression with nested objects
    """
    backends = create_test_backends("edge_complex_nested")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_complex_condition,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"user": {"tier": "premium", "credits": 100}},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "PREMIUM_USER" in signals
    assert "FREE_USER" not in signals

    backends.cleanup_all()


def test_router_complex_condition_free_user():
    """
    Complex condition evaluates to free user path
    """
    backends = create_test_backends("edge_complex_free")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_complex_condition,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"user": {"tier": "free", "credits": 0}},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "FREE_USER" in signals
    assert "PREMIUM_USER" not in signals

    backends.cleanup_all()


def test_router_boolean_true():
    """
    Boolean context value True triggers correct path
    """
    backends = create_test_backends("edge_bool_true")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_boolean_context,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"feature_enabled": True},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "ENABLED" in signals
    assert "DISABLED" not in signals

    backends.cleanup_all()


def test_router_boolean_false():
    """
    Boolean context value False triggers correct path
    """
    backends = create_test_backends("edge_bool_false")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_boolean_context,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"feature_enabled": False},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "DISABLED" in signals
    assert "ENABLED" not in signals

    backends.cleanup_all()


def test_router_null_value():
    """
    None/null value is correctly identified
    """
    backends = create_test_backends("edge_null")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_null_handling,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"nullable_field": None},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "NO_VALUE" in signals
    assert "HAS_VALUE" not in signals

    backends.cleanup_all()


def test_router_empty_string_value():
    """
    Empty string is correctly identified as no value
    """
    backends = create_test_backends("edge_empty_string")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_null_handling,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"nullable_field": ""},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "NO_VALUE" in signals
    assert "HAS_VALUE" not in signals

    backends.cleanup_all()


def test_router_non_empty_string_value():
    """
    Non-empty string is correctly identified as having value
    """
    backends = create_test_backends("edge_non_empty")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_null_handling,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"nullable_field": "some value"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "HAS_VALUE" in signals
    assert "NO_VALUE" not in signals

    backends.cleanup_all()


# ============================================================================
# Router CHAINING edge cases
# ============================================================================


def test_router_chain_all_steps():
    """
    Multiple routers in sequence all execute and emit signals
    """
    backends = create_test_backends("edge_chain")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=router_chain,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)
    assert "STEP_ONE_DONE" in signals
    assert "STEP_TWO_DONE" in signals
    assert "ALL_DONE" in signals

    backends.cleanup_all()
