import pytest
import os
from soe.local_backends import create_local_backends, create_in_memory_backends

class TestLocalStorageBackends:
    """
    Tests for local file-based backends.
    Uses tmp_path fixture to avoid writing to actual disk.
    """

    @pytest.fixture
    def backends(self, tmp_path):
        """Create local backends with temporary directories"""
        return create_local_backends(
            context_storage_dir=str(tmp_path / "contexts"),
            workflow_storage_dir=str(tmp_path / "workflows"),
            telemetry_storage_dir=str(tmp_path / "telemetry"),
            conversation_history_storage_dir=str(tmp_path / "conversations"),
            context_schema_storage_dir=str(tmp_path / "schemas"),
            identity_storage_dir=str(tmp_path / "identities"),
        )

    def test_context_backend(self, backends):
        execution_id = "test_exec_id"
        context_data = {"key": "value", "nested": {"a": 1}}

        # Save
        backends.context.save_context(execution_id, context_data)

        # Get
        loaded_context = backends.context.get_context(execution_id)
        assert loaded_context == context_data

        # Get non-existent
        assert backends.context.get_context("missing") == {}

    def test_workflow_backend(self, backends):
        execution_id = "test_exec_id"
        workflow_data = {"node1": {"type": "llm"}}
        workflow_name = "main_workflow"

        # Save Registry
        backends.workflow.save_workflows_registry(execution_id, workflow_data)

        # Get Registry
        loaded_registry = backends.workflow.soe_get_workflows_registry(execution_id)
        assert loaded_registry == workflow_data

        # Save Current Workflow Name
        backends.workflow.save_current_workflow_name(execution_id, workflow_name)

        # Get Current Workflow Name
        # Note: The method name might be get_current_workflow_name or similar, checking implementation...
        # Based on previous read, it likely exists.
        # Let's assume it is get_current_workflow_name based on usage in operational validation.
        loaded_name = backends.workflow.get_current_workflow_name(execution_id)
        assert loaded_name == workflow_name

    def test_telemetry_backend(self, backends):
        from datetime import datetime

        execution_id = "test_exec_id"
        event_type = "test_event"
        timestamp = datetime.utcnow().isoformat() + "Z"
        event_data = {"info": "something happened", "timestamp": timestamp}

        # Log event - caller provides timestamp
        backends.telemetry.log_event(execution_id, event_type, **event_data)

        # Get events
        # Assuming get_events exists and returns list of dicts
        events = backends.telemetry.get_events(execution_id)
        assert len(events) == 1
        assert events[0]["event_type"] == event_type
        assert events[0]["info"] == "something happened"
        assert "timestamp" in events[0]

    def test_conversation_history_backend(self, backends):
        execution_id = "test_exec_id"
        message = {"role": "user", "content": "hello"}

        # Add message
        backends.conversation_history.append_to_conversation_history(execution_id, message)

        # Get history
        history = backends.conversation_history.get_conversation_history(execution_id)
        assert len(history) == 1
        assert history[0] == message

    def test_context_schema_backend(self, backends):
        schema_name = "test_schema"
        schema_data = {"type": "object"}

        # Save context schema
        backends.context_schema.save_context_schema(schema_name, schema_data)

        # Get context schema
        loaded_schema = backends.context_schema.get_context_schema(schema_name)
        assert loaded_schema == schema_data

    def test_identity_backend(self, backends):
        """Test identity backend save/get/delete operations."""
        workflow_name = "test_workflow"
        identities = {
            "assistant": "You are a helpful assistant.",
            "coding_expert": "You are an expert programmer."
        }

        # Save identities
        backends.identity.save_identities(workflow_name, identities)

        # Get identities
        loaded_identities = backends.identity.get_identities(workflow_name)
        assert loaded_identities == identities

        # Get non-existent workflow
        assert backends.identity.get_identities("missing_workflow") is None

        # Delete identities
        result = backends.identity.delete_identities(workflow_name)
        assert result is True

        # Verify deleted
        assert backends.identity.get_identities(workflow_name) is None

        # Delete non-existent
        result = backends.identity.delete_identities(workflow_name)
        assert result is False

    def test_cleanup(self, backends, tmp_path):
        execution_id = "test_exec_id"
        backends.context.save_context(execution_id, {"a": 1})

        # Verify file exists
        assert (tmp_path / "contexts" / f"{execution_id}.json").exists()

        # Cleanup
        backends.cleanup_all()

        # Verify file is gone (or directory is empty/gone)
        # cleanup_all usually deletes the files or the directory content.
        # Let's check if the file is gone.
        assert not (tmp_path / "contexts" / f"{execution_id}.json").exists()

    def test_workflow_yaml_string_input(self, backends):
        """Test saving workflow from YAML string - must parse first now."""
        from soe.lib.yaml_parser import parse_yaml

        execution_id = "yaml_test"
        yaml_workflow = """
        node1:
          node_type: llm
          prompt: hello
        """
        # Caller must parse YAML before saving
        parsed = parse_yaml(yaml_workflow)
        backends.workflow.save_workflows_registry(execution_id, parsed)

        loaded = backends.workflow.soe_get_workflows_registry(execution_id)
        assert "node1" in loaded
        assert loaded["node1"]["node_type"] == "llm"

    def test_telemetry_get_events_empty(self, backends):
        """Test getting events for non-existent execution."""
        events = backends.telemetry.get_events("nonexistent")
        assert events == []

    def test_conversation_history_empty(self, backends):
        """Test getting conversation history for non-existent execution."""
        history = backends.conversation_history.get_conversation_history("nonexistent")
        assert history == []

    def test_context_schema_get_nonexistent(self, backends):
        """Test getting a non-existent context schema."""
        schema = backends.context_schema.get_context_schema("nonexistent_schema")
        assert schema is None

    def test_context_schema_save_and_get(self, backends):
        """Test saving and getting context schemas."""
        # Save context schema
        backends.context_schema.save_context_schema("test_schema", {"type": "object", "field": {"type": "string"}})

        # Get context schema
        schema = backends.context_schema.get_context_schema("test_schema")
        assert schema is not None
        assert schema["type"] == "object"

    def test_telemetry_cleanup(self, backends):
        """Test telemetry cleanup."""
        execution_id = "telemetry_cleanup"
        backends.telemetry.log_event(execution_id, "test_event", info="test")

        # Verify event exists
        events = backends.telemetry.get_events(execution_id)
        assert len(events) == 1

        # Cleanup
        backends.telemetry.cleanup_all()

        # Events should be gone
        events = backends.telemetry.get_events(execution_id)
        assert len(events) == 0

    def test_conversation_history_multiple_messages(self, backends):
        """Test appending multiple messages to conversation history."""
        identity = "multi_msg_test"

        # Append multiple messages
        backends.conversation_history.append_to_conversation_history(
            identity, {"role": "user", "content": "Hello"}
        )
        backends.conversation_history.append_to_conversation_history(
            identity, {"role": "assistant", "content": "Hi there!"}
        )

        # Get history
        history = backends.conversation_history.get_conversation_history(identity)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"


class TestInMemoryBackends:
    """
    Tests for in-memory backends to ensure full coverage.
    """

    @pytest.fixture
    def backends(self):
        """Create in-memory backends"""
        return create_in_memory_backends()

    def test_conversation_history_save_full(self, backends):
        """Test saving full conversation history."""
        identity = "test_identity"
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        # Save full history
        backends.conversation_history.save_conversation_history(identity, history)

        # Get and verify
        loaded = backends.conversation_history.get_conversation_history(identity)
        assert loaded == history

    def test_conversation_history_delete(self, backends):
        """Test deleting conversation history."""
        identity = "to_delete"
        backends.conversation_history.append_to_conversation_history(
            identity, {"role": "user", "content": "test"}
        )

        # Verify exists
        assert len(backends.conversation_history.get_conversation_history(identity)) == 1

        # Delete
        backends.conversation_history.delete_conversation_history(identity)

        # Verify gone
        assert len(backends.conversation_history.get_conversation_history(identity)) == 0

    def test_context_schema_delete(self, backends):
        """Test deleting context schema."""
        backends.context_schema.save_context_schema("to_delete", {"type": "object"})

        # Delete existing
        result = backends.context_schema.delete_context_schema("to_delete")
        assert result is True

        # Delete non-existent
        result = backends.context_schema.delete_context_schema("never_existed")
        assert result is False

    def test_context_schema_with_pydantic_model_via_lib(self, backends):
        """Test getting Pydantic model from context schema using lib function."""
        from soe.lib.schema_validation import get_pydantic_model_for_fields

        workflow_name = "model_test"
        schema = {
            "name": {"type": "string", "description": "A name"},
            "count": {"type": "integer", "description": "A count"},
            "active": {"type": "boolean", "description": "Is active"},
            "score": {"type": "number", "description": "A score"},
            "items": {"type": "array", "description": "Item list"},
            "data": {"type": "object", "description": "Data object"}
        }

        backends.context_schema.save_context_schema(workflow_name, schema)

        # Get schema and create model using lib
        retrieved_schema = backends.context_schema.get_context_schema(workflow_name)
        model = get_pydantic_model_for_fields(retrieved_schema, ["name", "count"])
        assert model is not None

        # Verify model can be instantiated
        instance = model(name="test", count=5)
        assert instance.name == "test"
        assert instance.count == 5

    def test_context_schema_pydantic_model_no_schema(self, backends):
        """Test getting Pydantic model when no schema exists."""
        from soe.lib.schema_validation import get_pydantic_model_for_fields

        schema = backends.context_schema.get_context_schema("no_such_workflow")
        model = get_pydantic_model_for_fields(schema, ["field"]) if schema else None
        assert model is None

    def test_context_schema_pydantic_model_no_matching_fields(self, backends):
        """Test getting Pydantic model when no fields match."""
        from soe.lib.schema_validation import get_pydantic_model_for_fields

        backends.context_schema.save_context_schema("test", {"existing": {"type": "string"}})

        schema = backends.context_schema.get_context_schema("test")
        model = get_pydantic_model_for_fields(schema, ["nonexistent"])
        assert model is None

    def test_workflow_get_nonexistent(self, backends):
        """Test getting workflow for non-existent execution."""
        registry = backends.workflow.soe_get_workflows_registry("nonexistent")
        # In-memory backend returns None for non-existent, storage backend returns {}
        assert registry is None or registry == {}

        name = backends.workflow.get_current_workflow_name("nonexistent")
        assert name == ""

    def test_identity_backend(self, backends):
        """Test in-memory identity backend operations."""
        workflow_name = "test_workflow"
        identities = {
            "assistant": "You are a helpful assistant."
        }

        # Save identities
        backends.identity.save_identities(workflow_name, identities)

        # Get identities
        loaded = backends.identity.get_identities(workflow_name)
        assert loaded == identities

        # Get non-existent
        assert backends.identity.get_identities("missing") is None

        # Delete
        result = backends.identity.delete_identities(workflow_name)
        assert result is True
        assert backends.identity.get_identities(workflow_name) is None

        # Delete non-existent
        result = backends.identity.delete_identities("already_gone")
        assert result is False

    def test_identity_cleanup(self, backends):
        """Test identity backend cleanup."""
        backends.identity.save_identities("workflow1", {"identity1": "test prompt"})
        backends.identity.save_identities("workflow2", {"identity2": "test prompt 2"})

        # Cleanup
        backends.identity.cleanup_all()

        # Verify all gone
        assert backends.identity.get_identities("workflow1") is None
        assert backends.identity.get_identities("workflow2") is None
