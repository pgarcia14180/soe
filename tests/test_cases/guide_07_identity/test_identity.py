"""
Identity tests for Guide Chapter 6.

These tests prove that identity enables conversation history
to persist across multiple LLM calls.

KEY INSIGHT: Identity is a boolean flag that enables conversation history.
All nodes with identity share history via main_execution_id.

Tests assert on BACKENDS:
- context: output fields stored correctly
- signals: correct signals emitted
- conversation_history: history accumulated properly
"""

import json
from typing import Dict, Any
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_llm_nodes, extract_signals, create_call_llm

from tests.test_cases.workflows.guide_identity import (
    MULTI_TURN_SAME_IDENTITY,
    MULTI_TURN_DIFFERENT_IDENTITY,
    MULTI_TURN_NO_IDENTITY,
    DYNAMIC_IDENTITY_MULTI_TURN,
    THREE_TURN_CONVERSATION,
)


class TestSameIdentitySharesHistory:
    """
    Test that nodes with SAME identity share conversation history.

    This is the core identity feature - when two LLM nodes use the
    same identity, the second node sees the first node's conversation.
    """

    def test_second_call_sees_first_conversation(self):
        """
        Two LLM nodes with same identity share conversation history.

        Assert on backends:
        - Context contains both responses
        - Signals show both nodes completed
        - Conversation history backend has 4 entries (2 user + 2 assistant)
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "Let me elaborate on that..."})
            else:
                return json.dumps({"firstResponse": "Technology is fascinating!"})

        backends = create_test_backends("same_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=MULTI_TURN_SAME_IDENTITY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "topic": "technology",
                "follow_up": "Tell me more"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert context["firstResponse"][-1] == "Technology is fascinating!"
        assert context["secondResponse"][-1] == "Let me elaborate on that..."

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "FIRST_COMPLETE" in signals
        assert "CONVERSATION_COMPLETE" in signals

        # Assert on conversation history backend
        # History is keyed by main_execution_id (which equals execution_id for root)
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 4, f"Expected 4 history entries (2 turns × 2 messages), got {len(history)}"

        # Verify first turn is in history
        assert any("technology" in str(entry.get("content", "")).lower() for entry in history), \
            "First turn prompt should be in history"
        assert any("fascinating" in str(entry.get("content", "")).lower() for entry in history), \
            "First turn response should be in history"

        backends.cleanup_all()


class TestDifferentIdentitiesShareHistory:
    """
    Test that nodes with DIFFERENT identity values still share history.

    This demonstrates that identity is a boolean flag, not a key.
    All nodes with any identity value share the same history.
    """

    def test_different_identity_values_share_history(self):
        """
        Two LLM nodes with different identity values share history.

        Assert on backends:
        - Both responses in context
        - Conversation history has entries from both calls
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "Continuing..."})
            else:
                return json.dumps({"firstResponse": "Starting conversation!"})

        backends = create_test_backends("different_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=MULTI_TURN_DIFFERENT_IDENTITY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "topic": "technology",
                "follow_up": "Tell me more"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert "firstResponse" in context
        assert "secondResponse" in context

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "FIRST_COMPLETE" in signals
        assert "CONVERSATION_COMPLETE" in signals

        # Assert on conversation history backend - BOTH calls contribute
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 4, f"Expected 4 history entries (both identities share), got {len(history)}"

        backends.cleanup_all()


class TestNoIdentityStateless:
    """
    Test that nodes WITHOUT identity have no history at all.

    This is the baseline - without identity, each LLM call
    is completely independent with empty conversation history.
    """

    def test_no_identity_means_no_history(self):
        """
        Two LLM nodes without identity have no shared history.

        Assert on backends:
        - Both responses in context
        - Conversation history backend is EMPTY
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "No memory..."})
            else:
                return json.dumps({"firstResponse": "Fresh start!"})

        backends = create_test_backends("no_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=MULTI_TURN_NO_IDENTITY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "topic": "technology",
                "follow_up": "Tell me more"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert "firstResponse" in context
        assert "secondResponse" in context

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "FIRST_COMPLETE" in signals
        assert "CONVERSATION_COMPLETE" in signals

        # Assert on conversation history backend - should be EMPTY
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 0, f"Expected empty history without identity, got {len(history)}"

        backends.cleanup_all()


class TestDynamicIdentity:
    """
    Test that identity can be any truthy value from context.

    The identity value itself doesn't matter - it just enables history.
    """

    def test_dynamic_identity_enables_history(self):
        """
        Identity templated from context enables history.

        Assert on backends:
        - Both responses in context
        - Conversation history has entries
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "second request" in prompt.lower():
                return json.dumps({"secondResult": "Second done"})
            else:
                return json.dumps({"firstResult": "First done"})

        backends = create_test_backends("dynamic_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=DYNAMIC_IDENTITY_MULTI_TURN,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "session_id": "user_alice_session_123",
                "request1": "First task",
                "request2": "Second task"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert context["firstResult"][-1] == "First done"
        assert context["secondResult"][-1] == "Second done"

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "FIRST_DONE" in signals
        assert "SECOND_DONE" in signals

        # Assert on conversation history backend - should have entries
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 4, f"Expected 4 history entries, got {len(history)}"

        backends.cleanup_all()


class TestHistoryAccumulates:
    """
    Test that conversation history grows with each turn.

    With three LLM calls using identity, each subsequent
    call should see more history from previous calls.
    """

    def test_three_turns_accumulate_history(self):
        """
        Three LLM nodes with identity accumulate history.

        Assert on backends:
        - All three responses in context
        - Conversation history has 6 entries (3 turns × 2 messages)
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Goodbye" in prompt:
                return json.dumps({"response3": "Third response"})
            elif "How are you" in prompt:
                return json.dumps({"response2": "Second response"})
            else:
                return json.dumps({"response1": "First response"})

        backends = create_test_backends("accumulating_history")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=THREE_TURN_CONVERSATION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "msg1": "Hello",
                "msg2": "How are you?",
                "msg3": "Goodbye"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert context["response1"][-1] == "First response"
        assert context["response2"][-1] == "Second response"
        assert context["response3"][-1] == "Third response"

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "TURN1_DONE" in signals
        assert "TURN2_DONE" in signals
        assert "TURN3_DONE" in signals

        # Assert on conversation history backend - 3 turns = 6 entries
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 6, f"Expected 6 history entries (3 turns × 2), got {len(history)}"

        # Verify all responses are in history
        history_str = str(history)
        assert "First response" in history_str
        assert "Second response" in history_str
        assert "Third response" in history_str

        backends.cleanup_all()
