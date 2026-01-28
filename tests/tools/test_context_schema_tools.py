import pytest
import json
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_get_context_schema import create_soe_get_context_schema_tool
from soe.builtin_tools.soe_inject_context_schema_field import create_soe_inject_context_schema_field_tool
from soe.builtin_tools.soe_remove_context_schema_field import create_soe_remove_context_schema_field_tool


def _setup_operational_context(backends, execution_id):
    """Helper to initialize operational context for telemetry."""
    backends.context.save_context(execution_id, {
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    })


# --- soe_get_context_schema tests ---

def test_soe_get_context_schema_returns_all():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string", "description": "User name"},
        "age": {"type": "integer", "description": "User age"}
    })

    get_tool = create_soe_get_context_schema_tool(execution_id, backends)
    result = get_tool()

    assert "name" in result
    assert "age" in result
    assert result["name"]["type"] == "string"
    assert result["age"]["type"] == "integer"


def test_soe_get_context_schema_specific_field():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string", "description": "User name"},
        "age": {"type": "integer", "description": "User age"}
    })

    get_tool = create_soe_get_context_schema_tool(execution_id, backends)
    result = get_tool(field_name="name")

    assert result["field_name"] == "name"
    assert result["definition"]["type"] == "string"
    assert result["definition"]["description"] == "User name"


def test_soe_get_context_schema_field_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string"}
    })

    get_tool = create_soe_get_context_schema_tool(execution_id, backends)
    result = get_tool(field_name="nonexistent")

    assert "error" in result
    assert "nonexistent" in result["error"]
    assert "available" in result


def test_soe_get_context_schema_empty():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    get_tool = create_soe_get_context_schema_tool(execution_id, backends)
    result = get_tool()

    assert result == {}


# --- soe_inject_context_schema_field tests ---

def test_soe_inject_context_schema_field_json():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    inject_tool = create_soe_inject_context_schema_field_tool(execution_id, backends)
    result = inject_tool(
        field_name="name",
        field_definition=json.dumps({"type": "string", "description": "User name"})
    )

    assert result["success"] is True
    assert result["action"] == "created"
    assert result["field_name"] == "name"

    schema = backends.context_schema.get_context_schema(execution_id)
    assert schema["name"]["type"] == "string"

    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_inject_context_schema_field"
    assert events[0]["context"]["action"] == "created"


def test_soe_inject_context_schema_field_yaml():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    inject_tool = create_soe_inject_context_schema_field_tool(execution_id, backends)
    result = inject_tool(
        field_name="name",
        field_definition="type: string\ndescription: User name"
    )

    assert result["success"] is True
    assert result["action"] == "created"

    schema = backends.context_schema.get_context_schema(execution_id)
    assert schema["name"]["type"] == "string"


def test_soe_inject_context_schema_field_updates_existing():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string", "description": "Old description"}
    })

    inject_tool = create_soe_inject_context_schema_field_tool(execution_id, backends)
    result = inject_tool(
        field_name="name",
        field_definition=json.dumps({"type": "string", "description": "New description"})
    )

    assert result["success"] is True
    assert result["action"] == "updated"

    schema = backends.context_schema.get_context_schema(execution_id)
    assert schema["name"]["description"] == "New description"

    events = backends.telemetry.get_events(execution_id)
    assert events[0]["context"]["action"] == "updated"


def test_soe_inject_context_schema_field_invalid_definition():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    inject_tool = create_soe_inject_context_schema_field_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Field definition must be a dictionary"):
        inject_tool(field_name="name", field_definition="invalid json")


def test_soe_inject_context_schema_field_first_field():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    inject_tool = create_soe_inject_context_schema_field_tool(execution_id, backends)
    result = inject_tool(
        field_name="first_field",
        field_definition=json.dumps({"type": "boolean"})
    )

    assert result["success"] is True
    assert result["action"] == "created"

    schema = backends.context_schema.get_context_schema(execution_id)
    assert len(schema) == 1
    assert schema["first_field"]["type"] == "boolean"


# --- soe_remove_context_schema_field tests ---

def test_soe_remove_context_schema_field_success():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    })

    remove_tool = create_soe_remove_context_schema_field_tool(execution_id, backends)
    result = remove_tool(field_name="name")

    assert result["removed"] is True
    assert result["field_name"] == "name"

    schema = backends.context_schema.get_context_schema(execution_id)
    assert "name" not in schema
    assert "age" in schema

    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_remove_context_schema_field"


def test_soe_remove_context_schema_field_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string"}
    })

    remove_tool = create_soe_remove_context_schema_field_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Field 'nonexistent' not found"):
        remove_tool(field_name="nonexistent")


def test_soe_remove_context_schema_field_empty_schema():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    remove_tool = create_soe_remove_context_schema_field_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Field 'name' not found"):
        remove_tool(field_name="name")


def test_soe_remove_context_schema_field_last_one():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.context_schema.save_context_schema(execution_id, {
        "name": {"type": "string"}
    })

    remove_tool = create_soe_remove_context_schema_field_tool(execution_id, backends)
    result = remove_tool(field_name="name")

    assert result["removed"] is True

    schema = backends.context_schema.get_context_schema(execution_id)
    assert schema == {}
