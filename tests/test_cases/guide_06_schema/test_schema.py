"""
Schema tests for Guide Chapter 5.

Tests that demonstrate schema validation with LLM output.
Schemas provide optional strong typing for context fields.

NOTE: Tests use combined config format where context_schema is included
in the config. This ensures schemas are automatically keyed by execution_id.
"""

import json
from typing import Dict, Any
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals

from tests.test_cases.workflows.guide_schema import (
    # Combined configs (preferred - includes context_schema)
    COMBINED_STRING_SCHEMA_CONFIG,
    COMBINED_INTEGER_SCHEMA_CONFIG,
    COMBINED_OBJECT_SCHEMA_CONFIG,
    COMBINED_MULTI_FIELD_CONFIG,
    COMBINED_TOOL_INTEGRATION_CONFIG,
    COMBINED_LIST_SCHEMA_CONFIG,
    COMBINED_BOOLEAN_SCHEMA_CONFIG,
    # Legacy separate definitions (for reference)
    SCHEMA_STRING_EXAMPLE,
    SCHEMA_STRING_DEFINITION,
    SCHEMA_INTEGER_EXAMPLE,
    SCHEMA_INTEGER_DEFINITION,
    SCHEMA_OBJECT_EXAMPLE,
    SCHEMA_OBJECT_DEFINITION,
    SCHEMA_LIST_EXAMPLE,
    SCHEMA_LIST_DEFINITION,
    SCHEMA_BOOLEAN_EXAMPLE,
    SCHEMA_BOOLEAN_DEFINITION,
    SCHEMA_MULTI_FIELD_EXAMPLE,
    SCHEMA_MULTI_FIELD_DEFINITION,
    SCHEMA_TOOL_INTEGRATION_EXAMPLE,
    SCHEMA_TOOL_INTEGRATION_DEFINITION,
    NO_SCHEMA_EXAMPLE,
)


class TestSchemaStringType:
    """Test schema validation with string output type."""

    def test_string_schema_validates_output(self):
        """
        Test that string schema validates LLM output.

        When a field has type 'string' in schema, the LLM
        output is validated as a string value.
        """
        def string_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({
                "summary": "This is a concise summary of the input text."
            })

        backends = create_test_backends("schema_string")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=string_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_STRING_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "A long text about technology."},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "SUMMARY_COMPLETE" in signals
        assert "summary" in context
        assert isinstance(context["summary"][-1], str)

        backends.cleanup_all()


class TestSchemaIntegerType:
    """Test schema validation with integer output type."""

    def test_integer_schema_validates_output(self):
        """
        Test that integer schema validates numeric LLM output.

        When a field has type 'integer' in schema, the output
        is validated and stored as an integer.
        """
        def integer_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({"word_count": 42})

        backends = create_test_backends("schema_integer")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=integer_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_INTEGER_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Some text with words."},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "COUNT_COMPLETE" in signals
        assert "word_count" in context
        assert context["word_count"][-1] == 42
        assert isinstance(context["word_count"][-1], int)

        backends.cleanup_all()


class TestSchemaObjectType:
    """Test schema validation with object/dict output type."""

    def test_object_schema_validates_output(self):
        """
        Test that object schema validates structured LLM output.

        When a field has type 'object' in schema, the output
        is validated as a dictionary/object.
        """
        def object_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({
                "person_data": {
                    "name": "Alice",
                    "age": 30
                }
            })

        backends = create_test_backends("schema_object")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=object_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_OBJECT_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Alice is 30 years old."},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "EXTRACTION_COMPLETE" in signals
        assert "person_data" in context
        assert context["person_data"][-1]["name"] == "Alice"
        assert context["person_data"][-1]["age"] == 30

        backends.cleanup_all()


class TestSchemaListType:
    """Test schema validation with list output type."""

    def test_list_schema_validates_output(self):
        """
        Test that list schema validates array LLM output.

        When a field has type 'list' in schema, the output
        is validated as a list/array.
        """
        def list_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({
                "keywords": ["python", "programming", "automation"]
            })

        backends = create_test_backends("schema_list")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=list_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_LIST_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Python programming for automation."},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "KEYWORDS_EXTRACTED" in signals
        assert "keywords" in context
        assert isinstance(context["keywords"][-1], list)
        assert len(context["keywords"][-1]) == 3

        backends.cleanup_all()


class TestSchemaBooleanType:
    """Test schema validation with boolean output type."""

    def test_boolean_schema_validates_output(self):
        """
        Test that boolean schema validates true/false LLM output.

        When a field has type 'boolean' in schema, the output
        is validated as a boolean value.
        """
        def boolean_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({"is_positive": True})

        backends = create_test_backends("schema_boolean")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=boolean_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_BOOLEAN_SCHEMA_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "I love this product!"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "SENTIMENT_CHECKED" in signals
        assert "is_positive" in context
        assert context["is_positive"][-1] is True

        backends.cleanup_all()


class TestSchemaMultipleFields:
    """Test schema with multiple field definitions."""

    def test_multi_field_schema_validates_chained_nodes(self):
        """
        Test schema with multiple fields across chained LLM nodes.

        When a workflow has multiple LLM nodes, each output
        field can have its own schema definition.
        """
        def multi_llm(prompt: str, config: Dict[str, Any]) -> str:
            if "topic" in prompt.lower() and "extract" in prompt.lower():
                return json.dumps({"topic": "Technology"})
            elif "summary" in prompt.lower() or "summarize" in prompt.lower():
                return json.dumps({"summary": "A brief summary about technology."})
            return json.dumps({"output": "default"})

        backends = create_test_backends("schema_multi_field")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=multi_llm)

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_MULTI_FIELD_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Technology is changing the world."},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "TOPIC_EXTRACTED" in signals
        assert "ANALYSIS_COMPLETE" in signals
        assert "topic" in context
        assert "summary" in context

        backends.cleanup_all()


class TestSchemaWithToolIntegration:
    """Test schema validation with tool integration."""

    def test_schema_enforces_tool_parameter_structure(self):
        """
        Test that schema-validated LLM output feeds into tools.

        Schemas ensure LLM output has the correct structure
        for downstream tool consumption.
        """
        def param_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({
                "params": {
                    "operation": "add",
                    "numbers": [10, 20, 30]
                }
            })

        def calculate(operation: str, numbers: list) -> dict:
            if operation == "add":
                return {"result": sum(numbers)}
            elif operation == "multiply":
                result = 1
                for n in numbers:
                    result *= n
                return {"result": result}
            return {"error": "Unknown operation"}

        tools_registry = {"calculate": calculate}

        backends = create_test_backends("schema_tool_integration")
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=param_llm, tools_registry=tools_registry
        )

        # Use combined config - schema is automatically saved keyed by execution_id
        execution_id = orchestrate(
            config=COMBINED_TOOL_INTEGRATION_CONFIG,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"user_request": "Add 10, 20, and 30"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "PARAMS_EXTRACTED" in signals
        assert "CALCULATED" in signals
        assert "result" in context
        assert context["result"][-1]["result"] == 60

        backends.cleanup_all()


class TestNoSchema:
    """Test that schemas are optional."""

    def test_workflow_works_without_schema(self):
        """
        Test that workflows work without any schema definition.

        Schemas are optional - LLM nodes work fine without them,
        the output just won't be type-validated.
        """
        def free_llm(prompt: str, config: Dict[str, Any]) -> str:
            return json.dumps({"output": "anything goes here"})

        backends = create_test_backends("no_schema")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=free_llm)

        execution_id = orchestrate(
            config=NO_SCHEMA_EXAMPLE,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input_text": "Some input"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        context = backends.context.get_context(execution_id)
        signals = extract_signals(backends, execution_id)

        assert "DONE" in signals
        assert "output" in context

        backends.cleanup_all()
