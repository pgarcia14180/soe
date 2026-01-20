"""
Schema edge case tests for Guide Chapter 5.

Tests for schema validation edge cases:
- Type coercion behavior
- Missing required fields
- Invalid type values

NOTE: Tests use combined config format where context_schema is included
in the config. This ensures schemas are automatically keyed by execution_id.
"""

import json
import pytest
from typing import Dict, Any
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals

from tests.test_cases.workflows.guide_schema import (
    # Combined configs (preferred)
    COMBINED_STRING_SCHEMA_CONFIG,
    COMBINED_INTEGER_SCHEMA_CONFIG,
    COMBINED_OBJECT_SCHEMA_CONFIG,
    COMBINED_LIST_SCHEMA_CONFIG,
    COMBINED_BOOLEAN_SCHEMA_CONFIG,
    # Legacy (for reference only)
    SCHEMA_STRING_EXAMPLE,
    SCHEMA_INTEGER_EXAMPLE,
    SCHEMA_INTEGER_DEFINITION,
    SCHEMA_OBJECT_EXAMPLE,
    SCHEMA_OBJECT_DEFINITION,
    SCHEMA_LIST_EXAMPLE,
    SCHEMA_LIST_DEFINITION,
    SCHEMA_BOOLEAN_EXAMPLE,
    SCHEMA_BOOLEAN_DEFINITION,
    NO_SCHEMA_EXAMPLE,
)


class TestSchemaTypeCoercion:
    """Test schema type coercion behavior."""

    def test_string_to_integer_coercion(self):
        """
        Test that numeric strings can be coerced to integers.

        When LLM returns "42" as a string but schema expects integer,
        the system should coerce it to an integer.
        """
        def string_number_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps("42")

        backends = create_test_backends("schema_coerce_string_to_int")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=string_number_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_INTEGER_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Test text"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "COUNT_COMPLETE" in signals
        assert isinstance(context["word_count"][-1], int)

        backends.cleanup_all()


class TestSchemaOptionalFields:
    """Test schema with optional vs required fields."""

    def test_workflow_continues_without_schema(self):
        """
        Test that missing schema doesn't block workflow.

        Schemas are optional - if no schema is defined for a field,
        the workflow continues normally.
        """
        def any_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({"output": {"nested": "value", "count": 5}})

        backends = create_test_backends("schema_optional")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=any_llm)

        execution_id = orchestrate(
            config=NO_SCHEMA_EXAMPLE,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Test"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "DONE" in signals
        assert "output" in context

        backends.cleanup_all()


class TestSchemaWithComplexObjects:
    """Test schema with complex nested objects."""

    def test_nested_object_preserved(self):
        """
        Test that nested object structure is preserved.

        When LLM returns deeply nested objects, the schema
        should preserve the complete structure.
        """
        def nested_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({
                "name": "Bob",
                "age": 25,
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                },
                "skills": ["python", "javascript"]
            })

        backends = create_test_backends("schema_nested_object")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=nested_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_OBJECT_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Bob, 25, NYC"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "EXTRACTION_COMPLETE" in signals
        assert context["person_data"][-1]["address"]["city"] == "NYC"
        assert "python" in context["person_data"][-1]["skills"]

        backends.cleanup_all()


class TestSchemaEmptyValues:
    """Test schema behavior with empty values."""

    def test_empty_string_is_valid(self):
        """
        Test that empty string is valid for string schema.

        An empty string "" is still a valid string value.
        """
        def empty_string_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps("")

        backends = create_test_backends("schema_empty_string")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=empty_string_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_STRING_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": ""},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "SUMMARY_COMPLETE" in signals
        assert context["summary"][-1] == ""

        backends.cleanup_all()

    def test_empty_list_is_valid(self):
        """
        Test that empty list is valid for list schema.

        An empty list [] is still a valid list value.
        """
        def empty_list_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps([])

        backends = create_test_backends("schema_empty_list")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=empty_list_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_LIST_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": ""},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "KEYWORDS_EXTRACTED" in signals
        assert context["keywords"][-1] == []

        backends.cleanup_all()


class TestSchemaZeroAndFalse:
    """Test schema behavior with zero and false values."""

    def test_zero_is_valid_integer(self):
        """
        Test that zero is valid for integer schema.

        Zero (0) is a valid integer value and should not be
        treated as missing or invalid.
        """
        def zero_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps(0)

        backends = create_test_backends("schema_zero_integer")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=zero_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_INTEGER_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": ""},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "COUNT_COMPLETE" in signals
        assert context["word_count"][-1] == 0

        backends.cleanup_all()

    def test_false_is_valid_boolean(self):
        """
        Test that false is valid for boolean schema.

        False is a valid boolean value and should not be
        treated as missing or invalid.
        """
        def false_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps(False)

        backends = create_test_backends("schema_false_boolean")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=false_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_BOOLEAN_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "I hate this"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "SENTIMENT_CHECKED" in signals
        assert context["is_positive"][-1] is False

        backends.cleanup_all()


class TestSchemaDescriptionField:
    """Test that schema descriptions are informational."""

    def test_description_does_not_affect_validation(self):
        """
        Test that description field is purely informational.

        The 'description' field in schema is for documentation
        and doesn't affect validation logic.
        """
        def simple_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps(100)

        # Custom combined config with long description
        config = """
workflows:
  example_workflow:
    CounterLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Count: {{ context.input_text }}"
      output_field: word_count
      event_emissions:
        - signal_name: COUNT_COMPLETE

context_schema:
  word_count:
    type: integer
    description: "This is a very long description that explains what the word count field represents and how it should be interpreted by downstream nodes."
"""

        backends = create_test_backends("schema_description")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=simple_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=config,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Test"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "COUNT_COMPLETE" in signals

        backends.cleanup_all()


class TestSchemaEnforcement:
    """Test that schemas are actually enforced by the LLM resolver."""

    def test_schema_backend_is_populated(self):
        """
        Test that context_schema from combined config is saved to backend.

        Verifies that the schema defined in config is actually stored
        in the context_schema backend keyed by execution_id.
        """
        def simple_llm(prompt: str, config: dict) -> str:
            return json.dumps(42)

        backends = create_test_backends("schema_backend_check")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=simple_llm)

        execution_id = orchestrate(
            config=COMBINED_INTEGER_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Test"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # Verify schema was saved to backend
        schema = backends.context_schema.get_context_schema(execution_id)
        assert schema is not None
        assert "word_count" in schema
        assert schema["word_count"]["type"] == "integer"

        backends.cleanup_all()


class TestAgentSchemaEdgeCases:
    """Edge cases for agent output schema validation."""

    def test_agent_schema_empty_string(self):
        """Agent output can be empty string when schema expects string."""
        from tests.test_cases.workflows.guide_schema import COMBINED_AGENT_SCHEMA_CONFIG
        from tests.test_cases.lib import create_agent_nodes, create_call_llm

        call_sequence = []

        def stub_llm(prompt: str, config: dict) -> str:
            is_router = '"available_tools":' in prompt
            is_parameter = '"tool_name":' in prompt and not is_router

            if is_router and len(call_sequence) == 0:
                call_sequence.append("router_1")
                return '{"action": "call_tool", "tool_name": "fetch_data"}'

            if is_parameter:
                call_sequence.append("param")
                return '{"query": "example"}'

            if is_router and len(call_sequence) >= 2:
                call_sequence.append("router_2")
                return '{"action": "finish"}'

            call_sequence.append("response")
            return '""'

        def fetch_data(query: str) -> dict:
            return {"data": f"result for {query}"}

        backends = create_test_backends("schema_agent_empty_string")
        call_llm = create_call_llm(stub=stub_llm)
        tools = [{"function": fetch_data, "max_retries": 0}]
        nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

        execution_id = orchestrate(
            config=COMBINED_AGENT_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"user_request": "Fetch data"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "AGENT_COMPLETE" in signals
        assert context["response"][-1] == ""

        backends.cleanup_all()

    def test_agent_schema_type_mismatch_retries(self):
        """Agent output type mismatch triggers retry until valid output is returned."""
        from tests.test_cases.workflows.guide_schema import COMBINED_AGENT_SCHEMA_CONFIG
        from tests.test_cases.lib import create_agent_nodes, create_call_llm

        call_sequence = []
        response_attempts = {"n": 0}

        def stub_llm(prompt: str, config: dict) -> str:
            is_router = '"available_tools":' in prompt
            is_parameter = '"tool_name":' in prompt and not is_router

            if is_router and len(call_sequence) == 0:
                call_sequence.append("router_1")
                return '{"action": "call_tool", "tool_name": "fetch_data"}'

            if is_parameter:
                call_sequence.append("param")
                return '{"query": "example"}'

            if is_router and len(call_sequence) >= 2:
                call_sequence.append("router_2")
                return '{"action": "finish"}'

            response_attempts["n"] += 1
            if response_attempts["n"] == 1:
                return '123'
            return '"valid response"'

        def fetch_data(query: str) -> dict:
            return {"data": f"result for {query}"}

        backends = create_test_backends("schema_agent_type_mismatch")
        call_llm = create_call_llm(stub=stub_llm)
        tools = [{"function": fetch_data, "max_retries": 0}]
        nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

        execution_id = orchestrate(
            config=COMBINED_AGENT_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"user_request": "Fetch data"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "AGENT_COMPLETE" in signals
        assert context["response"][-1] == "valid response"
        assert response_attempts["n"] > 1

        backends.cleanup_all()

    def test_schema_type_mismatch_triggers_retry(self):
        """
        Test that schema type mismatch triggers LLM retry.

        When LLM returns wrong type (string instead of integer),
        the resolver should retry. We verify by counting calls.
        """
        call_count = {"n": 0}

        def type_mismatch_llm(prompt: str, config: dict) -> str:
            call_count["n"] += 1
            # First call returns wrong type, subsequent calls return correct type
            if call_count["n"] == 1:
                return json.dumps("not an integer")
            return json.dumps(42)

        backends = create_test_backends("schema_type_mismatch")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=type_mismatch_llm)

        execution_id = orchestrate(
            config=COMBINED_INTEGER_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Test"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        # Workflow succeeded after retry
        assert "COUNT_COMPLETE" in signals
        assert context["word_count"][-1] == 42
        # LLM was called more than once due to type mismatch
        assert call_count["n"] > 1

        backends.cleanup_all()

    def test_persistent_type_mismatch_fails(self):
        """
        Test that persistent type mismatch exhausts retries.

        When LLM consistently returns wrong type, workflow should fail
        after max_retries are exhausted.
        """
        def always_wrong_llm(prompt: str, config: dict) -> str:
            # Always return wrong type
            return json.dumps("still not an integer")

        backends = create_test_backends("schema_persistent_mismatch")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=always_wrong_llm)

        # Should raise exception after max retries
        with pytest.raises(Exception) as exc_info:
            orchestrate(
                config=COMBINED_INTEGER_SCHEMA_CONFIG,
                initial_workflow_name="example_workflow",
                initial_signals=["START"],
                initial_context={"input_text": "Test"},
                backends=backends,
                broadcast_signals_caller=broadcast_signals_caller,
            )

        assert "retries" in str(exc_info.value).lower() or "exceeded" in str(exc_info.value).lower()

        backends.cleanup_all()
