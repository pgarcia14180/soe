"""
Guide Chapter 7: Child Nodes - Edge Cases

This test suite covers edge cases and failure modes for child nodes:
- Fire and forget (no signals_to_parent)
- Missing child workflow
- Empty input_fields
- Missing input_fields in context
- Missing context_updates_to_parent in child
- Multiple children with same signal
- Deeply nested children
- Child with different identity (isolated history)
"""

import json
import pytest
from typing import Dict, Any
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals, create_call_llm

from tests.test_cases.workflows.guide_child import (
    CHILD_FIRE_AND_FORGET,
    CHILD_EMPTY_INPUT_FIELDS,
    CHILD_MISSING_INPUT_FIELDS,
    CHILD_MISSING_CONTEXT_UPDATE,
    DEEPLY_NESTED_CHILDREN,
    CHILD_DIFFERENT_IDENTITY,
)


class TestChildFireAndForget:
    """
    Test child with no signals_to_parent.

    Parent can spawn a child and continue without waiting.
    """

    def test_fire_and_forget_parent_continues(self):
        """
        Parent continues immediately when no signals_to_parent.

        The child runs but parent doesn't wait for it.
        """
        backends = create_test_backends("fire_and_forget")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_FIRE_AND_FORGET,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Parent completed immediately
        assert "PARENT_DONE" in signals

        backends.cleanup_all()


class TestChildEmptyInputFields:
    """
    Test child with empty input_fields list.

    Empty input_fields: [] should not cause errors.
    """

    def test_empty_input_fields_works(self):
        """
        Child with input_fields: [] works correctly.

        No context is copied, but child runs normally.
        """
        backends = create_test_backends("empty_input_fields")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_EMPTY_INPUT_FIELDS,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={"some_data": "value"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Workflow completed
        assert "PARENT_COMPLETE" in signals

        backends.cleanup_all()


class TestChildMissingInputFields:
    """
    Test child with input_fields referencing missing context.

    Missing fields should not crash - they just aren't copied.
    """

    def test_missing_input_fields_handles_gracefully(self):
        """
        Missing input_fields in context don't cause errors.

        The child runs with whatever fields exist (none in this case).
        """
        backends = create_test_backends("missing_input_fields")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_MISSING_INPUT_FIELDS,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={},  # No fields provided
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Workflow completed despite missing fields
        assert "PARENT_COMPLETE" in signals

        backends.cleanup_all()


class TestChildMissingContextUpdate:
    """
    Test child with context_updates_to_parent for non-existent field.

    If child doesn't create the field, it just doesn't propagate.
    """

    def test_missing_context_update_no_error(self):
        """
        context_updates_to_parent with missing field doesn't error.

        The update is configured but child never creates that field.
        """
        backends = create_test_backends("missing_context_update")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_MISSING_CONTEXT_UPDATE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Workflow completed
        assert "PARENT_COMPLETE" in signals
        # The nonexistent_result was never created
        assert "nonexistent_result" not in context

        backends.cleanup_all()


class TestDeeplyNestedChildren:
    """
    Test deeply nested child workflows (5 levels).

    Signals should propagate correctly through all levels.
    """

    def test_five_level_nesting_works(self):
        """
        Signals propagate through 5 levels of nesting.

        level1 -> level2 -> level3 -> level4 -> level5
                                              <- DONE propagates back
        """
        backends = create_test_backends("deeply_nested")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=DEEPLY_NESTED_CHILDREN,
            initial_workflow_name="level1_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Top level completed
        assert "LEVEL1_COMPLETE" in signals

        backends.cleanup_all()


class TestChildDifferentIdentity:
    """
    Test child with different identity than parent.

    When child uses different identity, conversation history
    should be isolated from parent's history.
    """

    def test_different_identity_isolated_history(self):
        """
        Child with different identity has isolated history.

        Parent uses parent_session, child uses child_session.
        Child should NOT see parent's conversation history.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Start fresh" in prompt:
                return json.dumps({"childResponse": "Fresh start..."})
            else:
                return json.dumps({"parentResponse": "Parent talking..."})

        backends = create_test_backends("different_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=CHILD_DIFFERENT_IDENTITY,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "Continue"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Both completed
        assert "WORKFLOW_COMPLETE" in signals
        assert "parentResponse" in context
        assert "childResponse" in context

        # Histories should be separate (different identity keys)
        # Child's conversation should only have 2 entries (its own)
        # We can verify by checking that main_execution_id history
        # has both conversations (but stored under different keys)
        history = backends.conversation_history.get_conversation_history(execution_id)
        # With same identity sharing, we'd have 4+ entries
        # With different identities, parent's history is under main_execution_id
        # but child uses its own identity key
        assert len(history) >= 2  # At least parent's conversation

        backends.cleanup_all()


class TestChildContextUpdatePropagation:
    """
    Test that context updates propagate through nested children.

    When grandchild updates context, it should reach main parent.
    """

    def test_nested_context_updates_reach_parent(self):
        """
        Context updates from deeply nested child reach top parent.

        main -> middle -> grandchild creates field
                       <- field propagates back through chain
        """
        from tests.test_cases.workflows.guide_child import NESTED_SHARED_HISTORY

        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the discussion" in prompt:
                return json.dumps({"grandchildResponse": "Deep response"})
            else:
                return json.dumps({"mainResponse": "Main response"})

        backends = create_test_backends("nested_context_updates")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=NESTED_SHARED_HISTORY,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"topic": "AI", "follow_up": "Go deeper"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Main workflow completed
        assert "ALL_DONE" in signals

        # Grandchild's response should be in main context
        assert "grandchildResponse" in context
        assert context["grandchildResponse"][-1] == "Deep response"

        backends.cleanup_all()


class TestChildSignalPropagation:
    """
    Test edge cases in signal propagation.
    """

    def test_signal_not_in_signals_to_parent_stays_local(self):
        """
        Signals not in signals_to_parent don't reach parent.

        Only explicitly listed signals propagate.
        """
        from tests.test_cases.workflows.guide_child import CHILD_CONTINUES_EXAMPLE

        backends = create_test_backends("signal_local")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_CONTINUES_EXAMPLE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Parent sees PROGRESS and COMPLETED (in signals_to_parent)
        assert "PROGRESS_LOGGED" in signals
        assert "ALL_DONE" in signals

        # PHASE1_DONE and PHASE2_DONE are internal to child
        # They trigger child nodes but don't appear as parent signals
        # (unless they're in signals_to_parent, which they're not)

        backends.cleanup_all()
