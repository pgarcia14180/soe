import pytest
from soe.local_backends import create_in_memory_backends
from soe.builtin_tools.soe_get_identities import create_soe_get_identities_tool
from soe.builtin_tools.soe_inject_identity import create_soe_inject_identity_tool
from soe.builtin_tools.soe_remove_identity import create_soe_remove_identity_tool


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


# --- soe_get_identities tests ---

def test_soe_get_identities_returns_all():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful.",
        "expert": "You are an expert."
    })

    get_tool = create_soe_get_identities_tool(execution_id, backends)
    result = get_tool()

    assert "assistant" in result
    assert "expert" in result
    assert result["assistant"] == "You are helpful."
    assert result["expert"] == "You are an expert."


def test_soe_get_identities_list_only():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful.",
        "expert": "You are an expert."
    })

    get_tool = create_soe_get_identities_tool(execution_id, backends)
    result = get_tool(list_only=True)

    assert "identity_names" in result
    assert "assistant" in result["identity_names"]
    assert "expert" in result["identity_names"]


def test_soe_get_identities_specific():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful.",
        "expert": "You are an expert."
    })

    get_tool = create_soe_get_identities_tool(execution_id, backends)
    result = get_tool(identity_name="assistant")

    assert result["identity_name"] == "assistant"
    assert result["system_prompt"] == "You are helpful."


def test_soe_get_identities_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful."
    })

    get_tool = create_soe_get_identities_tool(execution_id, backends)
    result = get_tool(identity_name="nonexistent")

    assert "error" in result
    assert "nonexistent" in result["error"]
    assert "available" in result


def test_soe_get_identities_empty():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    get_tool = create_soe_get_identities_tool(execution_id, backends)
    result = get_tool()

    assert result == {}


def test_soe_get_identities_empty_list_only():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()

    get_tool = create_soe_get_identities_tool(execution_id, backends)
    result = get_tool(list_only=True)

    assert result == {"identity_names": []}


# --- soe_inject_identity tests ---

def test_soe_inject_identity_creates_new():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    inject_tool = create_soe_inject_identity_tool(execution_id, backends)
    result = inject_tool(identity_name="assistant", system_prompt="You are helpful.")

    assert result["success"] is True
    assert result["action"] == "created"
    assert result["identity_name"] == "assistant"

    identities = backends.identity.get_identities(execution_id)
    assert identities["assistant"] == "You are helpful."

    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_inject_identity"
    assert events[0]["context"]["action"] == "created"


def test_soe_inject_identity_updates_existing():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.identity.save_identities(execution_id, {
        "assistant": "Old prompt."
    })

    inject_tool = create_soe_inject_identity_tool(execution_id, backends)
    result = inject_tool(identity_name="assistant", system_prompt="New prompt.")

    assert result["success"] is True
    assert result["action"] == "updated"

    identities = backends.identity.get_identities(execution_id)
    assert identities["assistant"] == "New prompt."

    events = backends.telemetry.get_events(execution_id)
    assert events[0]["context"]["action"] == "updated"


def test_soe_inject_identity_first_identity():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    inject_tool = create_soe_inject_identity_tool(execution_id, backends)
    result = inject_tool(identity_name="first", system_prompt="First identity.")

    assert result["success"] is True
    assert result["action"] == "created"

    identities = backends.identity.get_identities(execution_id)
    assert len(identities) == 1
    assert identities["first"] == "First identity."


# --- soe_remove_identity tests ---

def test_soe_remove_identity_success():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful.",
        "expert": "You are an expert."
    })

    remove_tool = create_soe_remove_identity_tool(execution_id, backends)
    result = remove_tool(identity_name="assistant")

    assert result["removed"] is True
    assert result["identity_name"] == "assistant"

    identities = backends.identity.get_identities(execution_id)
    assert "assistant" not in identities
    assert "expert" in identities

    events = backends.telemetry.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_execution"
    assert events[0]["context"]["tool"] == "soe_remove_identity"


def test_soe_remove_identity_not_found():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful."
    })

    remove_tool = create_soe_remove_identity_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Identity 'nonexistent' not found"):
        remove_tool(identity_name="nonexistent")


def test_soe_remove_identity_empty_identities():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    remove_tool = create_soe_remove_identity_tool(execution_id, backends)

    with pytest.raises(ValueError, match="Identity 'assistant' not found"):
        remove_tool(identity_name="assistant")


def test_soe_remove_identity_last_one():
    execution_id = "test_exec_id"
    backends = create_in_memory_backends()
    _setup_operational_context(backends, execution_id)

    backends.identity.save_identities(execution_id, {
        "assistant": "You are helpful."
    })

    remove_tool = create_soe_remove_identity_tool(execution_id, backends)
    result = remove_tool(identity_name="assistant")

    assert result["removed"] is True

    identities = backends.identity.get_identities(execution_id)
    assert identities == {}
