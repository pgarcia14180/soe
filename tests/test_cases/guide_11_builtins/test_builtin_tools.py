"""
Guide Chapter 11: Built-in Tools

This test demonstrates built-in tools - always available tools that enable
self-evolution and introspection patterns in SOE workflows.

Learning Goals:
- Understanding built-in tools (no registration needed)
- Using soe_explore_docs for self-awareness
- Using soe_get_workflows for workflow introspection
- Using context tools for state management
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, setup_nodes, extract_signals
from tests.test_cases.workflows.guide_builtins import (
    builtin_soe_explore_docs,
    builtin_soe_explore_docs_search,
    builtin_soe_explore_docs_read,
    builtin_soe_get_workflows,
    builtin_soe_get_context,
    builtin_self_aware,
    builtin_soe_remove_workflow,
    builtin_soe_remove_node,
    builtin_soe_list_contexts,
    builtin_evolution_pattern,
    builtin_metacognitive,
    builtin_reflective,
    builtin_soe_call_tool,
    builtin_soe_get_available_tools,
    builtin_dynamic_tool_pattern,
)


# --- soe_explore_docs Tests ---

def test_soe_explore_docs_list():
    """
    Built-in soe_explore_docs lists documentation structure.
    No tool registration needed - it's always available.
    """
    backends = create_test_backends("builtin_soe_explore_docs_list")
    # Pass empty tools_registry to enable tool node type (built-ins are auto-resolved)
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_explore_docs,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "explore_params": {"path": "/", "action": "list"}
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # soe_explore_docs returns documentation listing
    assert "docs_list" in context
    docs_list = context["docs_list"][-1]
    assert "[DIR]" in docs_list or "[FILE]" in docs_list
    assert "DOCS_LISTED" in signals

    backends.cleanup_all()


def test_soe_explore_docs_search():
    """
    Built-in soe_explore_docs can search documentation.
    """
    backends = create_test_backends("builtin_soe_explore_docs_search")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_explore_docs_search,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "explore_params": {"path": "/", "action": "search", "query": "workflow"}
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Search results contain paths
    assert "search_results" in context
    search_results = context["search_results"][-1]
    assert "docs/" in search_results or "No results" in search_results
    assert "SEARCH_COMPLETE" in signals

    backends.cleanup_all()


def test_soe_explore_docs_read():
    """
    Built-in soe_explore_docs can read file content.
    """
    backends = create_test_backends("builtin_soe_explore_docs_read")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_explore_docs_read,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "explore_params": {"path": "docs/guide_01_tool.md", "action": "read"}
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Read returns file content
    assert "guide_content" in context
    guide_content = context["guide_content"][-1]
    assert len(guide_content) > 0
    assert "GUIDE_READ" in signals

    backends.cleanup_all()


# --- soe_get_workflows Tests ---

def test_soe_get_workflows():
    """
    Built-in soe_get_workflows returns registered workflow definitions.
    """
    backends = create_test_backends("builtin_soe_get_workflows")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_get_workflows,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # soe_get_workflows returns workflow structure
    assert "workflows_list" in context
    workflows_list = context["workflows_list"][-1]
    assert "example_workflow" in str(workflows_list)
    assert "WORKFLOWS_RETRIEVED" in signals

    backends.cleanup_all()


# --- get_context Tests ---

def test_get_context():
    """
    Built-in get_context returns current execution context.
    """
    backends = create_test_backends("builtin_get_context")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_get_context,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"initial_value": "test123"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # get_context returns context snapshot
    assert "current_context" in context
    current_context = context["current_context"][-1]
    # initial_value is stored as list in SOE context
    assert current_context.get("initial_value") == ["test123"]
    assert "CONTEXT_RETRIEVED" in signals

    backends.cleanup_all()


# --- Combined Self-Aware Test ---

def test_self_aware_workflow():
    """
    Workflow uses multiple built-ins to become self-aware.
    Explores docs, then queries its own workflow state.
    """
    backends = create_test_backends("builtin_self_aware")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_self_aware,
        initial_workflow_name="self_aware_workflow",
        initial_signals=["START"],
        initial_context={
            "explore_params": {"path": "/", "action": "tree"}
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Both steps completed
    assert "capabilities_tree" in context
    assert "current_workflows" in context
    assert "CAPABILITIES_KNOWN" in signals
    assert "STATE_KNOWN" in signals

    # Workflow can see itself
    workflows = context["current_workflows"][-1]
    assert "self_aware_workflow" in str(workflows)

    backends.cleanup_all()


# --- list_contexts Tests ---

def test_list_contexts():
    """
    Built-in list_contexts returns available execution contexts.
    """
    backends = create_test_backends("builtin_list_contexts")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_list_contexts,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # list_contexts returns list of context IDs
    assert "available_contexts" in context
    assert "CONTEXTS_LISTED" in signals

    backends.cleanup_all()


# --- reflective workflow Tests ---

def test_reflective_workflow():
    """
    Built-in get_context in reflective pattern.
    """
    backends = create_test_backends("builtin_reflective")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_reflective,
        initial_workflow_name="reflective_workflow",
        initial_signals=["START"],
        initial_context={"some_data": "test_value"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # get_context returns full state
    assert "full_state" in context
    full_state = context["full_state"][-1]
    assert "some_data" in full_state
    assert "STATE_GATHERED" in signals

    backends.cleanup_all()


# --- metacognitive workflow Tests ---

def test_metacognitive_workflow():
    """
    Metacognitive workflow discovers capabilities through soe_explore_docs.
    """
    backends = create_test_backends("builtin_metacognitive")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_metacognitive,
        initial_workflow_name="metacognitive_workflow",
        initial_signals=["START"],
        initial_context={
            "explore_params": {"path": "/", "action": "tree"}
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # soe_explore_docs returns capabilities tree
    assert "soe_capabilities" in context
    assert "CAPABILITIES_DISCOVERED" in signals

    backends.cleanup_all()


# --- evolution pattern Tests ---

def test_evolution_pattern():
    """
    Evolution pattern gets workflows state.
    """
    backends = create_test_backends("builtin_evolution")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    import json
    node_config = {
        "node_type": "router",
        "event_triggers": ["NEW_SIGNAL"],
        "event_emissions": [{"signal_name": "DONE"}]
    }

    execution_id = orchestrate(
        config=builtin_evolution_pattern,
        initial_workflow_name="evolving_workflow",
        initial_signals=["START"],
        initial_context={
            "designed_node": {
                "workflow_name": "evolving_workflow",
                "node_name": "NewNode",
                "node_config_data": json.dumps(node_config)
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Evolution completed
    assert "current_state" in context
    assert "STATE_ANALYZED" in signals
    assert "EVOLVED" in signals

    backends.cleanup_all()


# --- call_tool Tests ---

def test_call_tool():
    """
    Built-in call_tool dynamically invokes registered tools by name.
    """
    backends = create_test_backends("builtin_call_tool")

    # Register a simple test tool
    def test_echo(message: str) -> dict:
        return {"echo": message}

    tools_registry = {"test_echo": {"function": test_echo, "max_retries": 0}}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "test_echo",
                "arguments": '{"message": "hello world"}'
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # call_tool returns the result from the invoked tool
    assert "tool_result" in context
    tool_result = context["tool_result"][-1]
    # Result can be dict or JSON string depending on serialization
    if isinstance(tool_result, str):
        assert "success" in tool_result
        assert "hello world" in tool_result
    else:
        assert tool_result.get("success") is True
        assert tool_result.get("result", {}).get("echo") == "hello world"
    assert "TOOL_CALLED" in signals

    backends.cleanup_all()


def test_call_tool_not_found():
    """
    Built-in call_tool returns error for unknown tools.
    """
    backends = create_test_backends("builtin_call_tool_not_found")
    broadcast_signals_caller = setup_nodes(backends, tools_registry={})

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "nonexistent_tool",
                "arguments": "{}"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    tool_result = context["tool_result"][-1]

    # Should return error for unknown tool
    if isinstance(tool_result, str):
        assert "error" in tool_result
        assert "not found" in tool_result
    else:
        assert "error" in tool_result
        assert "not found" in tool_result["error"]

    backends.cleanup_all()


def test_call_tool_invalid_json():
    """
    Built-in call_tool returns error for invalid JSON arguments.
    """
    backends = create_test_backends("builtin_call_tool_invalid_json")

    def test_echo(message: str) -> dict:
        return {"echo": message}

    tools_registry = {"test_echo": {"function": test_echo, "max_retries": 0}}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "test_echo",
                "arguments": '{invalid json'  # Invalid JSON
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    tool_result = context["tool_result"][-1]

    # Should return error for invalid JSON
    if isinstance(tool_result, str):
        assert "error" in tool_result.lower()
        assert "json" in tool_result.lower()
    else:
        assert "error" in tool_result
        assert "JSON" in tool_result["error"]

    backends.cleanup_all()


def test_call_tool_callable_entry():
    """
    Built-in call_tool works when tool registry entry is a callable (not a dict).
    """
    backends = create_test_backends("builtin_call_tool_callable")

    def test_echo(message: str) -> dict:
        return {"echo": message}

    # Register tool as callable directly, not wrapped in dict
    tools_registry = {"test_echo": test_echo}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "test_echo",
                "arguments": '{"message": "hello callable"}'
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    tool_result = context["tool_result"][-1]

    # Should work with callable entry
    if isinstance(tool_result, str):
        assert "success" in tool_result
        assert "hello callable" in tool_result
    else:
        assert tool_result.get("success") is True
        assert tool_result.get("result", {}).get("echo") == "hello callable"

    backends.cleanup_all()


def test_call_tool_invalid_registry_entry():
    """
    Built-in call_tool returns error for invalid tool registry entry.
    """
    backends = create_test_backends("builtin_call_tool_invalid_entry")

    # Register something that's neither dict nor callable
    tools_registry = {"bad_tool": "not a function or dict"}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "bad_tool",
                "arguments": "{}"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    tool_result = context["tool_result"][-1]

    # Should return error for invalid entry
    if isinstance(tool_result, str):
        assert "error" in tool_result.lower()
    else:
        assert "error" in tool_result

    backends.cleanup_all()


def test_call_tool_non_callable_in_dict():
    """
    Built-in call_tool returns error when dict entry has non-callable function.
    """
    backends = create_test_backends("builtin_call_tool_non_callable")

    # Register a dict with a non-callable "function"
    tools_registry = {"bad_tool": {"function": "not a function"}}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "bad_tool",
                "arguments": "{}"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    tool_result = context["tool_result"][-1]

    # Should return error for non-callable
    if isinstance(tool_result, str):
        assert "error" in tool_result.lower()
        assert "not callable" in tool_result.lower()
    else:
        assert "error" in tool_result
        assert "not callable" in tool_result["error"]

    backends.cleanup_all()


def test_call_tool_argument_type_error():
    """
    Built-in call_tool returns error for argument type mismatch.
    """
    backends = create_test_backends("builtin_call_tool_type_error")

    def needs_int(count: int) -> dict:
        return {"count": count * 2}

    tools_registry = {"needs_int": {"function": needs_int, "max_retries": 0}}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_call_tool,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "needs_int",
                "arguments": '{"wrong_param": "value"}'  # Wrong param name
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    tool_result = context["tool_result"][-1]

    # Should return error for argument mismatch
    if isinstance(tool_result, str):
        assert "error" in tool_result.lower()
    else:
        assert "error" in tool_result

    backends.cleanup_all()


def test_soe_get_available_tools():
    """
    Built-in soe_get_available_tools lists registered tools.
    """
    backends = create_test_backends("builtin_soe_get_available_tools")

    # Register test tools
    def tool_a() -> dict:
        return {"a": True}

    def tool_b() -> dict:
        return {"b": True}

    tools_registry = {
        "tool_a": {"function": tool_a, "max_retries": 0},
        "tool_b": {"function": tool_b, "max_retries": 0},
    }
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_soe_get_available_tools,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # soe_get_available_tools returns list of tool names
    assert "available_tools" in context
    available = context["available_tools"][-1]
    assert "tool_a" in str(available)
    assert "tool_b" in str(available)
    assert "TOOLS_LISTED" in signals

    backends.cleanup_all()


def test_dynamic_tool_pattern():
    """
    Dynamic pattern: discover tools, then invoke one.
    """
    backends = create_test_backends("builtin_dynamic_pattern")

    def greet(name: str) -> dict:
        return {"greeting": f"Hello, {name}!"}

    tools_registry = {"greet": {"function": greet, "max_retries": 0}}
    broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

    execution_id = orchestrate(
        config=builtin_dynamic_tool_pattern,
        initial_workflow_name="dynamic_tool_workflow",
        initial_signals=["START"],
        initial_context={
            "tool_invocation": {
                "tool_name": "greet",
                "arguments": '{"name": "SOE"}'
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Both discovery and invocation completed
    assert "available_tools" in context
    assert "invocation_result" in context
    assert "TOOLS_DISCOVERED" in signals
    assert "INVOCATION_COMPLETE" in signals

    # Verify invocation result
    result = context["invocation_result"][-1]
    if isinstance(result, str):
        assert "success" in result
        assert "Hello, SOE!" in result
    else:
        assert result.get("success") is True
        assert "Hello, SOE!" in str(result.get("result"))

    backends.cleanup_all()
