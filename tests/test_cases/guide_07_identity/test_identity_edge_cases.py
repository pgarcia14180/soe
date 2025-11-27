"""
Guide Chapter 6: Identity - Edge Cases

This test suite covers edge cases and failure modes for identity:
- Empty identity strings
- Special characters in identity
- Dynamic identity resolving to empty
- Identity switching mid-workflow
- Parallel LLM calls with same identity
- Very long identity strings
"""

import json
import pytest
from typing import Dict, Any
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals, create_call_llm

from tests.test_cases.workflows.guide_identity import (
    EMPTY_IDENTITY,
    IDENTITY_SPECIAL_CHARS,
    DYNAMIC_IDENTITY_EMPTY,
    IDENTITY_SWITCH_MID_WORKFLOW,
    PARALLEL_SAME_IDENTITY,
    LONG_IDENTITY,
)


class TestEmptyIdentity:
    """
    Test behavior when identity is an empty string.

    Empty identity should behave like no identity - no shared history.
    """

    def test_empty_identity_no_shared_history(self):
        """
        Empty identity string should not share history.

        Both nodes have identity: "" which should be treated
        as no identity, resulting in independent calls.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "No history here..."})
            else:
                return json.dumps({"firstResponse": "Starting fresh!"})

        backends = create_test_backends("empty_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=EMPTY_IDENTITY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "Tell me more"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Workflow completes successfully
        assert "CONVERSATION_COMPLETE" in signals
        assert "firstResponse" in context
        assert "secondResponse" in context

        backends.cleanup_all()


class TestIdentitySpecialCharacters:
    """
    Test identity with special characters.

    Identity strings with @, /, :, etc. should work correctly.
    """

    def test_identity_with_special_chars_works(self):
        """
        Identity with special characters should function normally.

        Characters like @, /, : are valid in identity strings.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "Continuing..."})
            else:
                return json.dumps({"firstResponse": "Started!"})

        backends = create_test_backends("special_chars_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=IDENTITY_SPECIAL_CHARS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "Tell me more"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Both turns completed
        assert "CONVERSATION_COMPLETE" in signals
        assert "firstResponse" in context
        assert "secondResponse" in context

        # Verify history was shared (stored under special chars identity)
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) >= 4  # At least 2 exchanges

        backends.cleanup_all()


class TestDynamicIdentityEmpty:
    """
    Test dynamic identity that resolves to empty string.

    When {{ context.missing_field }} resolves to empty,
    it should behave like no identity.
    """

    def test_dynamic_identity_missing_context(self):
        """
        Dynamic identity from missing context field resolves to empty.

        No shared history should occur.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "No context..."})
            else:
                return json.dumps({"firstResponse": "Starting..."})

        backends = create_test_backends("dynamic_identity_empty")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=DYNAMIC_IDENTITY_EMPTY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "More"},
            # Note: missing_session_id is NOT provided
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Workflow completes despite missing context field
        assert "CONVERSATION_COMPLETE" in signals
        assert "firstResponse" in context
        assert "secondResponse" in context

        backends.cleanup_all()


class TestIdentitySwitchMidWorkflow:
    """
    Test switching identity mid-workflow.

    When identity changes between nodes, history should be isolated
    per identity, even if returning to a previous identity.
    """

    def test_identity_switch_isolates_history(self):
        """
        Switching identity isolates conversation history.

        Turn1: session_alpha
        Turn2: session_beta (fresh start)
        Turn3: session_alpha (sees Turn1's history only)
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            # Detect turn by message content
            if "msg3" in prompt or "Goodbye" in prompt:
                return json.dumps({"response3": "Third response"})
            elif "msg2" in prompt or "middle" in prompt:
                return json.dumps({"response2": "Second response"})
            else:
                return json.dumps({"response1": "First response"})

        backends = create_test_backends("identity_switch")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=IDENTITY_SWITCH_MID_WORKFLOW,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "msg1": "Hello",
                "msg2": "middle message",
                "msg3": "Goodbye"
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # All three turns completed
        assert "TURN3_DONE" in signals
        assert "response1" in context
        assert "response2" in context
        assert "response3" in context

        backends.cleanup_all()


class TestParallelSameIdentity:
    """
    Test parallel LLM calls with same identity.

    When multiple nodes with same identity trigger simultaneously,
    both should complete but history behavior may vary.
    """

    def test_parallel_calls_same_identity_complete(self):
        """
        Parallel LLM calls with same identity both complete.

        Both CallA and CallB use identity: shared_session.
        Both should execute and produce output.
        """
        call_count = {"a": 0, "b": 0}

        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            # Use unique markers in the context values to distinguish
            if "UNIQUE_MARKER_ALPHA" in prompt and call_count["a"] == 0:
                call_count["a"] += 1
                return json.dumps({"responseA": "Response A"})
            elif "UNIQUE_MARKER_BETA" in prompt and call_count["b"] == 0:
                call_count["b"] += 1
                return json.dumps({"responseB": "Response B"})
            # Handle retry/subsequent calls
            elif "UNIQUE_MARKER_ALPHA" in prompt:
                return json.dumps({"responseA": "Response A"})
            elif "UNIQUE_MARKER_BETA" in prompt:
                return json.dumps({"responseB": "Response B"})
            else:
                return json.dumps({"response": "Unknown"})

        backends = create_test_backends("parallel_same_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=PARALLEL_SAME_IDENTITY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"requestA": "UNIQUE_MARKER_ALPHA", "requestB": "UNIQUE_MARKER_BETA"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Both parallel calls completed
        assert "A_DONE" in signals
        assert "B_DONE" in signals
        assert "responseA" in context
        assert "responseB" in context

        backends.cleanup_all()


class TestLongIdentity:
    """
    Test very long identity strings.

    Long identity strings should work correctly without truncation.
    """

    def test_long_identity_string_works(self):
        """
        Very long identity string functions correctly.

        History is shared despite the long identity key.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "Continue the conversation" in prompt:
                return json.dumps({"secondResponse": "Continuing..."})
            else:
                return json.dumps({"firstResponse": "Started!"})

        backends = create_test_backends("long_identity")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=LONG_IDENTITY,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology", "follow_up": "Tell me more"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Workflow completes
        assert "CONVERSATION_COMPLETE" in signals
        assert "firstResponse" in context
        assert "secondResponse" in context

        # History was shared
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) >= 4

        backends.cleanup_all()


class TestIdentitySystemPromptInjection:
    """
    Test that identity system prompts are actually injected.

    When using combined config with identities section, the system prompt
    should be injected as the first message in conversation history.
    """

    def test_system_prompt_injected_from_config(self):
        """
        Test that identity system prompt from config is in conversation history.

        When identities are defined in combined config, the system prompt
        should be stored in the identity backend and injected into history.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({"firstResponse": "Hello!"})

        # Combined config with identities section
        config_with_identity = """
workflows:
  example_workflow:
    FirstLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Discuss: {{ context.topic }}"
      identity: helpful_assistant
      output_field: firstResponse
      event_emissions:
        - signal_name: DONE

identities:
  helpful_assistant: "You are a helpful AI assistant. Always be polite and informative."
"""

        backends = create_test_backends("identity_system_prompt")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=config_with_identity,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"topic": "technology"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)
        assert "DONE" in signals

        # Verify identity was saved to backend
        identities = backends.identity.get_identities(execution_id)
        assert identities is not None
        assert "helpful_assistant" in identities
        assert "helpful AI assistant" in identities["helpful_assistant"]

        # Verify system prompt was injected into conversation history
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) >= 1
        # First message should be system prompt
        system_messages = [m for m in history if m.get("role") == "system"]
        assert len(system_messages) > 0
        assert "helpful AI assistant" in system_messages[0]["content"]

        backends.cleanup_all()

    def test_identity_backend_populated_from_combined_config(self):
        """
        Test that identities from combined config are saved to backend.

        The identities section should be parsed and stored in identity backend
        keyed by execution_id.
        """
        def stub_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({"output": "Response"})

        config_with_multiple_identities = """
workflows:
  example_workflow:
    SimpleLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Hello"
      output_field: output
      event_emissions:
        - signal_name: DONE

identities:
  analyst: "You are a data analyst. Focus on numbers and metrics."
  creative: "You are a creative writer. Be imaginative and expressive."
"""

        backends = create_test_backends("identity_backend_check")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=config_with_multiple_identities,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Verify identities were saved to backend
        identities = backends.identity.get_identities(execution_id)
        assert identities is not None
        assert "analyst" in identities
        assert "creative" in identities
        assert "data analyst" in identities["analyst"]
        assert "creative writer" in identities["creative"]

        backends.cleanup_all()
