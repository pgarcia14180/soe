"""
Suborchestration tests for Guide Chapter 7.

Tests that demonstrate child nodes for modular
workflow composition and parent-child communication.
"""

import json
from typing import Dict, Any
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals, create_call_llm

from tests.test_cases.workflows.guide_child import (
    CHILD_SIMPLE_EXAMPLE,
    CHILD_INPUT_FIELDS_EXAMPLE,
    CHILD_CONTEXT_UPDATES_EXAMPLE,
    CHILD_CONTINUES_EXAMPLE,
    MULTIPLE_CHILDREN_EXAMPLE,
    NESTED_CHILDREN_EXAMPLE,
    CHILD_WITH_LLM_EXAMPLE,
)


class TestChildSimple:
    """Test basic child node spawning."""

    def test_simple_child_completes(self):
        """
        Test that parent spawns child and receives completion signal.

        The child workflow runs independently and signals back
        to the parent when done.
        """
        backends = create_test_backends("child_simple")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_SIMPLE_EXAMPLE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "WORKFLOW_COMPLETE" in signals

        backends.cleanup_all()


class TestChildInputFields:
    """Test passing data from parent to child."""

    def test_input_fields_passed_to_child(self):
        """
        Test that input_fields are copied to child context.

        Parent can pass specific context fields to child
        using input_fields configuration.
        """
        backends = create_test_backends("child_input_fields")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=CHILD_INPUT_FIELDS_EXAMPLE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={"data_to_process": "important_data"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PARENT_COMPLETE" in signals

        backends.cleanup_all()


class TestChildContextUpdates:
    """Test receiving data from child to parent."""

    def test_context_updates_propagate_to_parent(self):
        """
        Test that context_updates_to_parent enables child-to-parent data flow.

        Child can write to context fields that propagate
        back to parent context via configured updates.
        """
        def sum_numbers_tool(numbers: list) -> int:
            return sum(numbers)

        tools_registry = {"sum_numbers": sum_numbers_tool}

        backends = create_test_backends("child_context_updates")
        nodes, broadcast_signals_caller = create_nodes(backends, tools_registry=tools_registry)

        execution_id = orchestrate(
            config=CHILD_CONTEXT_UPDATES_EXAMPLE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={"calc_params": {"numbers": [1, 2, 3, 4, 5]}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PARENT_COMPLETE" in signals

        backends.cleanup_all()


class TestChildContinues:
    """Test that child can continue after calling parent."""

    def test_child_continues_after_callback(self):
        """
        Test that child workflow continues after signaling parent.

        signals_to_parent is NOT a "done" signal - child can
        keep working after notifying parent.
        """
        backends = create_test_backends("child_continues")
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

        assert "PROGRESS_LOGGED" in signals
        assert "ALL_DONE" in signals

        backends.cleanup_all()


class TestMultipleChildren:
    """Test spawning multiple child workflows."""

    def test_multiple_children_run_concurrently(self):
        """
        Test that multiple children can run from same trigger.

        Multiple child nodes triggered by START will spawn
        their respective child workflows.
        """
        backends = create_test_backends("multiple_children")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=MULTIPLE_CHILDREN_EXAMPLE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "ALL_WORKERS_DONE" in signals

        backends.cleanup_all()


class TestNestedChildren:
    """Test nested parent-child-grandchild workflows."""

    def test_three_level_nesting(self):
        """
        Test that grandchild signals propagate through child to main.

        main_workflow -> child_workflow -> grandchild_workflow
                      <-                <-
        """
        backends = create_test_backends("nested_children")
        nodes, broadcast_signals_caller = create_nodes(backends)

        execution_id = orchestrate(
            config=NESTED_CHILDREN_EXAMPLE,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "MAIN_COMPLETE" in signals

        backends.cleanup_all()


class TestChildWithLLM:
    """Test child workflow with LLM node."""

    def test_child_with_llm_returns_result(self):
        """
        Test that child with LLM can analyze and signal completion.

        Child workflows can contain any node type including
        LLM nodes for AI-powered sub-tasks.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({
                "analysisResult": "The text discusses technology trends."
            })

        backends = create_test_backends("child_with_llm")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=CHILD_WITH_LLM_EXAMPLE,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={"textToAnalyze": "AI is changing everything."},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PARENT_DONE" in signals

        backends.cleanup_all()


class TestChildSharedConversationHistory:
    """
    Test that child workflows share conversation history with parent.

    This is the key feature: when identity is set on LLM nodes,
    children inherit main_execution_id and share the same
    conversation history as the parent.

    Tests assert on BACKENDS:
    - context: output fields stored correctly
    - signals: correct signals emitted
    - conversation_history: history accumulated across parent/child boundary
    """

    def test_child_sees_parent_conversation_history(self):
        """
        Child LLM node should see parent's conversation in history.

        Parent calls LLM first, then spawns child with same identity.
        Child's LLM call should have access to parent's conversation.

        Assert on backends:
        - Context contains both responses
        - Signals show workflow completed
        - Conversation history has 4 entries (2 turns × 2 messages)
        """
        from tests.test_cases.workflows.guide_child import CHILD_SHARED_HISTORY

        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"childResponse": "Let me elaborate on that..."})
            else:
                return json.dumps({"parentResponse": "Technology is fascinating!"})

        backends = create_test_backends("child_shared_history")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=CHILD_SHARED_HISTORY,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "Tell me more"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert context["parentResponse"][-1] == "Technology is fascinating!"
        assert context["childResponse"][-1] == "Let me elaborate on that..."

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "WORKFLOW_COMPLETE" in signals

        # Assert on conversation history backend
        # Both parent and child LLM calls stored under main_execution_id
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 4, f"Expected 4 history entries (2 turns × 2 messages), got {len(history)}"

        # Verify both responses are in history
        history_str = str(history)
        assert "Technology is fascinating" in history_str
        assert "elaborate" in history_str

        backends.cleanup_all()

    def test_three_turn_parent_child_shared_history(self):
        """
        Three LLM calls (2 parent + 1 child) share conversation history.

        Parent: Turn 1 -> Turn 2 -> Spawn Child -> Child Turn
        All 3 calls should accumulate in same conversation history.

        Assert on backends:
        - Context contains all 3 responses
        - Conversation history has 6 entries (3 turns × 2 messages)
        """
        from tests.test_cases.workflows.guide_child import CHILD_THREE_TURN_SHARED_HISTORY

        call_count = [0]

        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return json.dumps({"parentResponse1": "First parent response"})
            elif call_count[0] == 2:
                return json.dumps({"parentResponse2": "Second parent response"})
            else:
                return json.dumps({"childResponse": "Child continues conversation"})

        backends = create_test_backends("three_turn_shared")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=CHILD_THREE_TURN_SHARED_HISTORY,
            initial_workflow_name="parent_workflow",
            initial_signals=["START"],
            initial_context={
                "topic": "technology",
                "parent_followup": "Tell me more",
                "child_question": "What about the future?"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend - all 3 responses present
        context = backends.context.get_context(execution_id)
        assert context["parentResponse1"][-1] == "First parent response"
        assert context["parentResponse2"][-1] == "Second parent response"
        assert context["childResponse"][-1] == "Child continues conversation"

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "WORKFLOW_COMPLETE" in signals

        # Assert on conversation history backend - 3 turns = 6 entries
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 6, f"Expected 6 history entries (3 turns × 2), got {len(history)}"

        # Verify all responses are in history
        history_str = str(history)
        assert "First parent response" in history_str
        assert "Second parent response" in history_str
        assert "Child continues conversation" in history_str

        backends.cleanup_all()

    def test_grandchild_sees_full_history(self):
        """
        Grandchild should see parent's conversation history.

        main -> child -> grandchild
        Grandchild's LLM call should have access to main's conversation.

        Assert on backends:
        - Context contains both responses
        - Conversation history has all accumulated entries
        """
        from tests.test_cases.workflows.guide_child import NESTED_SHARED_HISTORY

        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the discussion" in prompt:
                return json.dumps({"grandchildResponse": "Building on what we discussed..."})
            else:
                return json.dumps({"mainResponse": "Let's discuss technology!"})

        backends = create_test_backends("nested_shared_history")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=NESTED_SHARED_HISTORY,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "Go deeper"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend
        context = backends.context.get_context(execution_id)
        assert context["mainResponse"][-1] == "Let's discuss technology!"
        assert context["grandchildResponse"][-1] == "Building on what we discussed..."

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "ALL_DONE" in signals

        # Assert on conversation history backend
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 4, f"Expected 4 history entries (2 turns × 2), got {len(history)}"

        # Verify both responses in history
        history_str = str(history)
        assert "Let's discuss technology" in history_str
        assert "Building on what we discussed" in history_str

        backends.cleanup_all()

    def test_four_turn_nested_shared_history(self):
        """
        Four LLM calls across main, child (2 turns), and grandchild.

        main (1 turn) -> child (2 turns) -> grandchild (1 turn)
        All 4 calls should accumulate in same conversation history.

        Assert on backends:
        - Context contains all 4 responses
        - Conversation history has 8 entries (4 turns × 2 messages)
        """
        from tests.test_cases.workflows.guide_child import NESTED_FOUR_TURN_SHARED_HISTORY

        call_count = [0]

        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return json.dumps({"mainResponse": "Main discussion started"})
            elif call_count[0] == 2:
                return json.dumps({"childResponse1": "Child first response"})
            elif call_count[0] == 3:
                return json.dumps({"childResponse2": "Child second response"})
            else:
                return json.dumps({"grandchildResponse": "Grandchild final response"})

        backends = create_test_backends("four_turn_nested")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=NESTED_FOUR_TURN_SHARED_HISTORY,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={
                "topic": "technology",
                "child_msg1": "First child question",
                "child_msg2": "Second child question",
                "grandchild_msg": "Grandchild question"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Assert on context backend - all 4 responses present
        context = backends.context.get_context(execution_id)
        assert context["mainResponse"][-1] == "Main discussion started"
        assert context["childResponse1"][-1] == "Child first response"
        assert context["childResponse2"][-1] == "Child second response"
        assert context["grandchildResponse"][-1] == "Grandchild final response"

        # Assert on signals
        signals = extract_signals(backends, execution_id)
        assert "ALL_DONE" in signals

        # Assert on conversation history backend - 4 turns = 8 entries
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 8, f"Expected 8 history entries (4 turns × 2), got {len(history)}"

        # Verify all responses are in history
        history_str = str(history)
        assert "Main discussion started" in history_str
        assert "Child first response" in history_str
        assert "Child second response" in history_str
        assert "Grandchild final response" in history_str

        backends.cleanup_all()
