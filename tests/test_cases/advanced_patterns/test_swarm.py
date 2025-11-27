"""
Tests for Advanced Patterns: Swarm Intelligence

Tests voting and consensus patterns:
1. Simple consensus with threshold
2. Deterministic voting with multiple voters
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals
from tests.test_cases.workflows.advanced_swarm import (
    simple_consensus,
    deterministic_voting,
)


def test_consensus_reached():
    """Test consensus when threshold is met"""
    backends = create_test_backends("consensus_reached")
    nodes, broadcast_signals_caller = create_nodes(backends)

    execution_id = orchestrate(
        config=simple_consensus,
        initial_workflow_name="consensus_workflow",
        initial_signals=["START"],
        initial_context={
            "approve_count": 5,
            "threshold": 3,
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    assert "CONSENSUS_REACHED" in signals
    assert "CONSENSUS_FAILED" not in signals

    backends.cleanup_all()


def test_consensus_failed():
    """Test consensus when threshold is not met"""
    backends = create_test_backends("consensus_failed")
    nodes, broadcast_signals_caller = create_nodes(backends)

    execution_id = orchestrate(
        config=simple_consensus,
        initial_workflow_name="consensus_workflow",
        initial_signals=["START"],
        initial_context={
            "approve_count": 2,
            "threshold": 3,
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    assert "CONSENSUS_FAILED" in signals
    assert "CONSENSUS_REACHED" not in signals

    backends.cleanup_all()


def test_voting_approved():
    """Test voting with majority approval"""
    backends = create_test_backends("voting_approved")
    nodes, broadcast_signals_caller = create_nodes(backends)

    execution_id = orchestrate(
        config=deterministic_voting,
        initial_workflow_name="voting_workflow",
        initial_signals=["START"],
        initial_context={
            "votes": [
                {"voter": "A", "vote": "approve"},
                {"voter": "B", "vote": "approve"},
                {"voter": "C", "vote": "reject"},
            ]
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    assert "APPROVED" in signals
    assert "REJECTED" not in signals
    assert "DONE" in signals

    backends.cleanup_all()


def test_voting_rejected():
    """Test voting with majority rejection"""
    backends = create_test_backends("voting_rejected")
    nodes, broadcast_signals_caller = create_nodes(backends)

    execution_id = orchestrate(
        config=deterministic_voting,
        initial_workflow_name="voting_workflow",
        initial_signals=["START"],
        initial_context={
            "votes": [
                {"voter": "A", "vote": "reject"},
                {"voter": "B", "vote": "approve"},
                {"voter": "C", "vote": "reject"},
            ]
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    assert "REJECTED" in signals
    assert "APPROVED" not in signals
    assert "DONE" in signals

    backends.cleanup_all()
