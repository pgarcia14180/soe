"""
Node creation helpers for tests.

Usage patterns:

1. Simple test (only orchestrate, no broadcast_signals):
   broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)
   execution_id = orchestrate(..., broadcast_signals_caller=broadcast_signals_caller)

2. Test needing broadcast_signals (for mid-execution signals):
   nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)
   execution_id = orchestrate(..., broadcast_signals_caller=broadcast_signals_caller)
   broadcast_signals(execution_id, ["SIGNAL"], nodes, backends)
"""

import copy
from typing import Callable, Dict, Any, Tuple, Optional, List, Union
from soe import broadcast_signals, orchestrate
from soe.nodes.router.factory import create_router_node_caller
from soe.nodes.llm.factory import create_llm_node_caller
from soe.nodes.agent.factory import create_agent_node_caller
from soe.nodes.tool.factory import create_tool_node_caller
from soe.nodes.child.factory import create_child_node_caller
from soe.lib.yaml_parser import parse_yaml
from soe.types import CallLlm, Backends


def create_orchestrate_caller(nodes: Dict[str, Any]) -> Callable:
    """Create orchestrate caller function that supports sub-orchestration.

    This is a convenience wrapper that creates a fully-wired orchestrate caller
    with the broadcast_signals function already configured.

    Args:
        nodes: Dictionary mapping node types to their caller functions

    Returns:
        A callable that can start workflow executions
    """

    def orchestrate_caller(
        config: Union[str, Dict[str, Any]],
        initial_workflow_name: str,
        initial_signals: List[str],
        initial_context: Dict[str, Any],
        backends: Backends,
    ) -> str:
        """Start a new workflow execution."""
        if isinstance(config, str):
            parsed_config = parse_yaml(config)
        else:
            parsed_config = copy.deepcopy(config)

        def broadcast_signals_caller(execution_id: str, signals: List[str]):
            broadcast_signals(execution_id, signals, nodes, backends)

        execution_id = orchestrate(
            config=parsed_config,
            initial_workflow_name=initial_workflow_name,
            initial_signals=initial_signals,
            initial_context=initial_context,
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        return execution_id

    return orchestrate_caller


def create_nodes(
    backends,
    call_llm: Optional[CallLlm] = None,
    tools_registry: Optional[Dict[str, Callable]] = None,
) -> Tuple[Dict[str, Callable], Callable]:
    """
    Create all node types for tests.

    Args:
        backends: LocalBackends instance
        call_llm: Optional LLM caller function
        tools_registry: Optional dict mapping tool name -> callable

    Returns:
        Tuple of (nodes dict, broadcast_signals_caller function)
    """
    nodes = {}

    def broadcast_signals_caller(id: str, signals):
        broadcast_signals(id, signals, nodes, backends)

    # Router always available
    nodes["router"] = create_router_node_caller(backends, broadcast_signals_caller)

    # LLM and Agent if call_llm provided
    if call_llm is not None:
        nodes["llm"] = create_llm_node_caller(backends, call_llm, broadcast_signals_caller)
        tools_list = []
        if tools_registry:
            tools_list = [{"function": func, "max_retries": 0} for func in tools_registry.values()]
        nodes["agent"] = create_agent_node_caller(backends, tools_list, call_llm, broadcast_signals_caller)

    # Tool if tools_registry provided (even if empty, to test validation)
    if tools_registry is not None:
        nodes["tool"] = create_tool_node_caller(backends, tools_registry, broadcast_signals_caller)

    # Child always available (needs orchestrate_caller)
    orchestrate_caller = create_orchestrate_caller(nodes)
    nodes["child"] = create_child_node_caller(backends, orchestrate_caller)

    return nodes, broadcast_signals_caller


def setup_nodes(
    backends,
    call_llm: Optional[CallLlm] = None,
    tools_registry: Optional[Dict[str, Callable]] = None,
) -> Callable:
    """
    Create nodes and return only the broadcast_signals_caller.

    Use this when you only need to call orchestrate() and don't need
    to call broadcast_signals() manually (most common case).

    Args:
        backends: LocalBackends instance
        call_llm: Optional LLM caller function
        tools_registry: Optional dict mapping tool name -> callable

    Returns:
        broadcast_signals_caller function for use with orchestrate()

    Example:
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)
        execution_id = orchestrate(..., broadcast_signals_caller=broadcast_signals_caller)
    """
    _, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm, tools_registry=tools_registry)
    return broadcast_signals_caller


# Convenience aliases for common test setups
def create_router_nodes(backends) -> Tuple[Dict[str, Callable], Callable]:
    return create_nodes(backends)


def create_llm_nodes(backends, call_llm: CallLlm) -> Tuple[Dict[str, Callable], Callable]:
    return create_nodes(backends, call_llm=call_llm)


def create_agent_nodes(
    backends,
    call_llm: CallLlm,
    tools: list = None
) -> Tuple[Dict[str, Callable], Callable]:
    tools_registry = {}
    if tools:
        for tool_config in tools:
            func = tool_config["function"]
            tools_registry[func.__name__] = func
    return create_nodes(backends, call_llm=call_llm, tools_registry=tools_registry)


def create_tool_nodes(
    backends,
    tools_registry: Dict[str, Callable]
) -> Tuple[Dict[str, Callable], Callable]:
    return create_nodes(backends, tools_registry=tools_registry)
