"""
Agent node factory

Orchestrates the multi-stage loop (Router -> Response/Parameter -> Execution)
using the AgentLoopState for internal tracking.
"""

from typing import Dict, Any, Callable, List
from .state import get_operational_state, prepare_agent_context
from .lib.loop_state import AgentLoopState
from .lib.tools import load_tools_and_build_signatures
from .lib.loop_handlers import handle_finish_action, handle_tool_call_action
from .stages import execute_router_stage
from ..lib.signal_emission import emit_completion_signals, handle_llm_failure
from ...types import BroadcastSignalsCaller, AgentNodeCaller, EventTypes
from ...lib.register_event import register_event
from ..lib.context import save_output_to_context
from ...validation.operational import validate_operational
from .validation import validate_node_config


def create_agent_node_caller(
    backends,
    tools: List[Dict[str, Any]],
    call_llm: Callable,
    broadcast_signals_caller: BroadcastSignalsCaller,
) -> AgentNodeCaller:
    """
    Create agent node caller with pre-loaded dependencies.

    Args:
        backends: Backend services
        tools: List of tool configs, each with {"function": callable, "max_retries": int, "failure_signal": str}
        call_llm: LLM caller function
        broadcast_signals_caller: Signal broadcaster
    """
    tools_registry: Dict[str, Dict[str, Any]] = {
        tool_config["function"].__name__: tool_config for tool_config in tools
    }

    def execute_agent_node(execution_id: str, node_config: Dict[str, Any]) -> None:
        validate_operational(execution_id, backends)
        validate_node_config(node_config)

        operational_state = get_operational_state(execution_id, node_config, backends)

        register_event(backends, execution_id, EventTypes.LLM_CALL, {"stage": "router"})

        loop_state = AgentLoopState.create(
            history_key=operational_state.history_key,
            backends=backends,
            max_retries=operational_state.max_retries
        )

        agent_context = prepare_agent_context(execution_id, node_config, backends, loop_state.tool_responses)
        tools_signature = load_tools_and_build_signatures(
            agent_context.tool_names, tools_registry, execution_id, backends
        )

        register_event(
            backends=backends,
            execution_id=execution_id,
            event_type=EventTypes.AGENT_TOOLS_LOADED,
            data={
                "node_name": node_config.get("name", "unknown"),
                "agent_tools": agent_context.tool_names,
                "registry_tools": list(tools_registry.keys()),
            }
        )

        while loop_state.can_retry():
            router_response = execute_router_stage(
                call_llm=call_llm,
                agent_context=agent_context,
                loop_state=loop_state,
                tools_signature=tools_signature,
                config=node_config,
                max_retries=operational_state.max_retries,
            )

            if router_response.action == "finish":
                final_response = handle_finish_action(
                    call_llm=call_llm,
                    agent_context=agent_context,
                    loop_state=loop_state,
                    node_config=node_config,
                    backends=backends,
                    operational_state=operational_state,
                )

                save_output_to_context(execution_id, operational_state.output_field, final_response.output, backends)

                if operational_state.output_field:
                    if operational_state.output_field in operational_state.context:
                        operational_state.context[operational_state.output_field].append(final_response.output)
                    else:
                        operational_state.context[operational_state.output_field] = [final_response.output]

                emit_completion_signals(
                    selected_signal=final_response.selected_signal,
                    node_config=node_config,
                    operational_state=operational_state,
                    broadcast_signals_caller=broadcast_signals_caller,
                    execution_id=execution_id,
                )
                return

            elif router_response.action == "call_tool":
                handle_tool_call_action(
                    call_llm=call_llm,
                    tool_name=router_response.tool_name,
                    tools_registry=tools_registry,
                    agent_context=agent_context,
                    loop_state=loop_state,
                    node_config=node_config,
                    operational_state=operational_state,
                    backends=backends,
                    execution_id=execution_id,
                )

        error_msg = f"Agent execution exceeded max retries ({loop_state.max_retries})."
        if loop_state.errors:
            error_msg += f" Last error: {loop_state.errors[-1]}"

        handle_llm_failure(
            failure_signal=operational_state.llm_failure_signal,
            error_message=error_msg,
            node_type="agent",
            execution_id=execution_id,
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

    return execute_agent_node
