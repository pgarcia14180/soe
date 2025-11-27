"""
Guide Chapter 1: Basics - Simple Router

This test demonstrates the most basic SOE concept: a Router node that
conditionally emits signals based on context data.

Learning Goals:
- Understanding node_type: router
- Understanding event_triggers (how nodes activate)
- Understanding event_emissions (how nodes produce signals)
- Understanding Jinja2 conditions in workflows
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_router_nodes, extract_signals
from tests.test_cases.workflows.guide_router import (
    simple_router_validation,
    simple_router_unconditional,
)


def test_router_with_valid_input():
    """
    Router emits VALID_INPUT when user_input exists
    """
    backends = create_test_backends("router_valid")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=simple_router_validation,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"user_input": "Hello, SOE!"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    assert "VALID_INPUT" in signals
    assert "INVALID_INPUT" not in signals
    assert context["user_input"][-1] == "Hello, SOE!"

    backends.cleanup_all()


def test_router_with_invalid_input():
    """
    Router emits INVALID_INPUT when user_input is missing
    """
    backends = create_test_backends("router_invalid")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=simple_router_validation,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},  # No user_input
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    assert "INVALID_INPUT" in signals
    assert "VALID_INPUT" not in signals
    assert "__operational__" in context
    assert "error" not in context.get("__operational__", {})

    backends.cleanup_all()


def test_router_unconditional_signal():
    """
    Router emits signals without conditions (always fires)
    """
    backends = create_test_backends("router_unconditional")
    nodes, broadcast_signals_caller = create_router_nodes(backends)

    execution_id = orchestrate(
        config=simple_router_unconditional,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"some_data": "value"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    signals = extract_signals(backends, execution_id)

    assert "CONTINUE" in signals

    # Verify telemetry captured execution
    telemetry_events = backends.telemetry.get_events(execution_id)
    event_types = [e.get("event_type") for e in telemetry_events]
    assert "node_execution" in event_types

    backends.cleanup_all()
