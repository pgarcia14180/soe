"""
Tests for Appendix A: Operational Features

These tests demonstrate operational context access, AND logic for signals,
and loop prevention patterns.
"""

import os
import pytest
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_router_nodes, create_llm_nodes, extract_signals
from tests.test_cases.workflows.appendix_a_operational import (
    WAIT_FOR_MULTIPLE_SIGNALS,
    LOOP_PREVENTION,
    LLM_WITH_RETRIES,
)


class TestWaitForMultipleSignals:
    """Tests for AND logic with signals."""

    def test_waits_for_both_signals(self):
        """
        Both tasks must complete before BOTH_COMPLETE is emitted.

        The WaitForBoth router triggers on either A_DONE OR B_DONE,
        but only emits BOTH_COMPLETE when BOTH are in operational signals.
        """
        backends = create_test_backends("wait_for_both")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=WAIT_FOR_MULTIPLE_SIGNALS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Should have both individual signals and the combined signal
        assert "A_DONE" in signals
        assert "B_DONE" in signals
        assert "BOTH_COMPLETE" in signals

        backends.cleanup_all()


class TestLoopPrevention:
    """Tests for loop prevention pattern."""

    def test_loop_eventually_stops(self):
        """
        Loop should stop after max iterations.

        The LoopingNode checks __operational__.nodes.get('LoopingNode', 0)
        and stops when it exceeds the limit.
        """
        backends = create_test_backends("loop_prevention")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=LOOP_PREVENTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Loop limit should be reached
        assert "LOOP_LIMIT_REACHED" in signals

        # Should have some CONTINUE signals but not infinite
        continue_count = signals.count("CONTINUE")
        assert continue_count >= 1
        assert continue_count <= 5  # Max is 5

        backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Tests deliberate failure patterns that real LLMs won't produce"
)
class TestLLMRetries:
    """Tests for LLM retry behavior."""

    def test_llm_retries_on_invalid_response(self):
        """
        LLM node retries when response fails validation.

        First call returns invalid JSON, retry returns valid JSON.
        The workflow completes successfully.
        """
        call_count = {"n": 0}

        def flaky_llm(prompt: str, config: dict) -> str:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return "not valid json"  # First call fails
            return '{"result": "Success after retry"}'  # Retry succeeds

        backends = create_test_backends("llm_retries")
        nodes, broadcast_signals_caller = create_llm_nodes(backends, flaky_llm)

        execution_id = orchestrate(
            config=LLM_WITH_RETRIES,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input": "test data"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Workflow completed successfully after retry
        assert "DONE" in signals
        assert context["result"][-1] == "Success after retry"
        assert call_count["n"] == 2  # First failed, second succeeded

        backends.cleanup_all()
