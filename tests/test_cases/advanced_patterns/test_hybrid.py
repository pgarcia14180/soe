"""
Tests for Advanced Patterns: Hybrid Intelligence

Tests mixing deterministic routers with tools/LLMs:
1. Input validation → Process → Output validation
2. Safety rails pattern
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals
from tests.test_cases.workflows.advanced_hybrid import (
    deterministic_hybrid,
)


def process_input(user_input: str) -> dict:
    """Tool that processes input and validates it"""
    if len(user_input) > 5:
        return {"valid": True, "processed": user_input.upper()}
    else:
        return {"valid": False, "error": "Input too short"}


def test_hybrid_valid_flow():
    """Test hybrid pattern with valid input and valid output"""
    backends = create_test_backends("hybrid_valid")

    tools_registry = {"process_input": process_input}
    nodes, broadcast_signals_caller = create_nodes(
        backends,
        tools_registry=tools_registry
    )

    execution_id = orchestrate(
        config=deterministic_hybrid,
        initial_workflow_name="hybrid_workflow",
        initial_signals=["START"],
        initial_context={
            "user_input": "Hello World",
            "process_params": {"user_input": "Hello World"},
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Verify the full flow: INPUT_VALID → PROCESSED → OUTPUT_VALID → DONE
    assert "INPUT_VALID" in signals
    assert "PROCESSED" in signals
    assert "OUTPUT_VALID" in signals
    assert "DONE" in signals
    assert "ERROR" not in signals

    # Verify the tool ran
    assert context["processed_result"][-1]["valid"] == True
    assert context["processed_result"][-1]["processed"] == "HELLO WORLD"

    backends.cleanup_all()


def test_hybrid_invalid_input():
    """Test hybrid pattern with invalid input (empty)"""
    backends = create_test_backends("hybrid_invalid_input")

    tools_registry = {"process_input": process_input}
    nodes, broadcast_signals_caller = create_nodes(
        backends,
        tools_registry=tools_registry
    )

    execution_id = orchestrate(
        config=deterministic_hybrid,
        initial_workflow_name="hybrid_workflow",
        initial_signals=["START"],
        initial_context={
            "user_input": "",  # Empty input
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # Verify input validation caught the error
    assert "INPUT_INVALID" in signals
    assert "ERROR" in signals
    assert "PROCESSED" not in signals

    backends.cleanup_all()


def test_hybrid_invalid_output():
    """Test hybrid pattern where tool returns invalid output"""
    backends = create_test_backends("hybrid_invalid_output")

    tools_registry = {"process_input": process_input}
    nodes, broadcast_signals_caller = create_nodes(
        backends,
        tools_registry=tools_registry
    )

    execution_id = orchestrate(
        config=deterministic_hybrid,
        initial_workflow_name="hybrid_workflow",
        initial_signals=["START"],
        initial_context={
            "user_input": "Hi",  # Too short, tool returns valid=False
            "process_params": {"user_input": "Hi"},
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Verify output validation caught the error
    assert "INPUT_VALID" in signals
    assert "PROCESSED" in signals
    assert "OUTPUT_INVALID" in signals
    assert "ERROR" in signals
    assert "DONE" not in signals

    # Verify the tool ran but returned invalid
    assert context["processed_result"][-1]["valid"] == False

    backends.cleanup_all()
