"""
Convenience initialization for SOE.

This module provides easy setup functions for common use cases.
Use these to quickly get started without manually wiring nodes and backends.
"""

import copy
from typing import Callable, Dict, Any, Tuple, Optional, List, Union
from .broker import broadcast_signals, orchestrate
from .nodes.router.factory import create_router_node_caller
from .nodes.llm.factory import create_llm_node_caller
from .nodes.agent.factory import create_agent_node_caller
from .nodes.tool.factory import create_tool_node_caller
from .nodes.child.factory import create_child_node_caller
from .lib.yaml_parser import parse_yaml
from .types import CallLlm, Backends
from .local_backends import create_in_memory_backends, create_local_backends


def create_all_nodes(
    backends: Backends,
    call_llm: Optional[CallLlm] = None,
    tools_registry: Optional[Dict[str, Callable]] = None,
) -> Tuple[Dict[str, Callable], Callable]:
    """
    Create all node types with automatic wiring.

    This is the recommended way to set up nodes for orchestration.
    Returns both the nodes dictionary and the broadcast_signals_caller.

    Args:
        backends: Backend services (use create_in_memory_backends or create_local_backends)
        call_llm: Optional LLM caller function for LLM/Agent nodes
        tools_registry: Optional dict mapping tool name -> callable for Tool/Agent nodes

    Returns:
        Tuple of (nodes dict, broadcast_signals_caller function)

    Example:
        backends = create_in_memory_backends()
        nodes, broadcast = create_all_nodes(backends, call_llm=my_llm, tools_registry=my_tools)

        execution_id = orchestrate(
            config=workflow_yaml,
            initial_workflow_name="my_workflow",
            initial_signals=["START"],
            initial_context={"user_input": "Hello"},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )
    """
    nodes = {}

    def broadcast_signals_caller(id: str, signals: List[str]):
        broadcast_signals(id, signals, nodes, backends)

    nodes["router"] = create_router_node_caller(backends, broadcast_signals_caller)

    if call_llm is not None:
        nodes["llm"] = create_llm_node_caller(backends, call_llm, broadcast_signals_caller)

        tools_list = []
        if tools_registry:
            tools_list = [{"function": func, "max_retries": 0} for func in tools_registry.values()]
        nodes["agent"] = create_agent_node_caller(backends, tools_list, call_llm, broadcast_signals_caller)

    if tools_registry is not None:
        nodes["tool"] = create_tool_node_caller(backends, tools_registry, broadcast_signals_caller)

    def orchestrate_caller(
        config: Union[str, Dict[str, Any]],
        initial_workflow_name: str,
        initial_signals: List[str],
        initial_context: Dict[str, Any],
        backends: Backends,
    ) -> str:
        """Start a child workflow execution."""
        if isinstance(config, str):
            parsed_config = parse_yaml(config)
        else:
            parsed_config = copy.deepcopy(config)

        def child_broadcast(execution_id: str, signals: List[str]):
            broadcast_signals(execution_id, signals, nodes, backends)

        return orchestrate(
            config=parsed_config,
            initial_workflow_name=initial_workflow_name,
            initial_signals=initial_signals,
            initial_context=initial_context,
            backends=backends,
            broadcast_signals_caller=child_broadcast,
        )

    nodes["child"] = create_child_node_caller(backends, orchestrate_caller)

    return nodes, broadcast_signals_caller


def setup_orchestration(
    call_llm: Optional[CallLlm] = None,
    tools_registry: Optional[Dict[str, Callable]] = None,
    use_local_storage: bool = False,
    storage_dir: str = "./orchestration_data",
) -> Tuple[Backends, Callable]:
    """
    One-line setup for SOE orchestration.

    Creates backends and nodes with automatic wiring.
    Returns the backends and broadcast_signals_caller ready to use.

    Args:
        call_llm: Optional LLM caller function for LLM/Agent nodes
        tools_registry: Optional dict mapping tool name -> callable
        use_local_storage: If True, use file-based storage. If False, use in-memory.
        storage_dir: Directory for local storage (only used if use_local_storage=True)

    Returns:
        Tuple of (backends, broadcast_signals_caller)

    Example:
        # Minimal setup (router-only workflows)
        backends, broadcast = setup_orchestration()

        # Full setup with LLM and tools
        backends, broadcast = setup_orchestration(
            call_llm=my_llm_function,
            tools_registry={"search": search_fn, "calculate": calc_fn},
        )

        execution_id = orchestrate(
            config=workflow_yaml,
            initial_workflow_name="my_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )
    """
    if use_local_storage:
        backends = create_local_backends(
            context_storage_dir=f"{storage_dir}/contexts",
            workflow_storage_dir=f"{storage_dir}/workflows",
            telemetry_storage_dir=f"{storage_dir}/telemetry",
            conversation_history_storage_dir=f"{storage_dir}/conversations",
            context_schema_storage_dir=f"{storage_dir}/schemas",
            identity_storage_dir=f"{storage_dir}/identities",
        )
    else:
        backends = create_in_memory_backends()

    _, broadcast_signals_caller = create_all_nodes(
        backends=backends,
        call_llm=call_llm,
        tools_registry=tools_registry,
    )

    return backends, broadcast_signals_caller


__all__ = [
    "create_all_nodes",
    "setup_orchestration",
]
