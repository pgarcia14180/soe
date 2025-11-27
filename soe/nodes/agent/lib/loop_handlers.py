"""
Agent loop action handlers

Focused functions for handling each router action type.
Extracted from factory.py to keep the main loop clean.
"""

from typing import Dict, Any, Callable, TYPE_CHECKING
from ..stages import (
    execute_response_stage,
    execute_parameter_stage,
    FinalResponse,
)
from ...lib.tools import create_tool_schema
from ...lib.output import get_signal_options, get_output_model

if TYPE_CHECKING:
    from ..types import CallLlm
    from .loop_state import AgentLoopState
    from ..state import AgentContext, AgentOperationalState
    from ....types import Backends


def handle_finish_action(
    call_llm: "CallLlm",
    agent_context: "AgentContext",
    loop_state: "AgentLoopState",
    node_config: Dict[str, Any],
    backends: "Backends",
    operational_state: "AgentOperationalState",
) -> FinalResponse:
    """Handle the 'finish' action from the router."""
    signal_options = get_signal_options(operational_state.event_emissions)
    output_model = get_output_model(
        backends, operational_state.main_execution_id, operational_state.output_field
    )

    return execute_response_stage(
        call_llm=call_llm,
        agent_context=agent_context,
        loop_state=loop_state,
        config=node_config,
        output_field=operational_state.output_field,
        output_schema=output_model,
        signal_options=signal_options,
        max_retries=operational_state.max_retries,
    )


def handle_tool_call_action(
    call_llm: "CallLlm",
    tool_name: str,
    tools_registry: Dict[str, Dict[str, Any]],
    agent_context: "AgentContext",
    loop_state: "AgentLoopState",
    node_config: Dict[str, Any],
    operational_state: "AgentOperationalState",
    backends: "Backends",
    execution_id: str,
) -> bool:
    """Handle the 'call_tool' action from the router."""
    from ....lib.register_event import register_event
    from ....local_backends import EventTypes

    if not tool_name or tool_name not in tools_registry:
        register_event(
            backends=backends,
            execution_id=execution_id,
            event_type=EventTypes.AGENT_TOOL_NOT_FOUND,
            data={
                "node_name": node_config.get("name", "unknown"),
                "tool_name": tool_name,
                "available_tools": list(tools_registry.keys()),
            }
        )
        loop_state.add_system_error(f"Tool '{tool_name}' not found or not available.")
        return False

    tool_config = tools_registry[tool_name]
    tool_func = tool_config["function"]
    tool_exec_retries = tool_config.get("max_retries", 0)
    tool_schema = create_tool_schema(tool_func)

    try:
        tool_args = execute_parameter_stage(
            call_llm=call_llm,
            agent_context=agent_context,
            loop_state=loop_state,
            tool_name=tool_name,
            tool_schema=tool_schema,
            config=node_config,
            max_retries=operational_state.max_retries,
        )

        tool_args_dict = tool_args.model_dump() if hasattr(tool_args, 'model_dump') else dict(tool_args)

        register_event(
            backends=backends,
            execution_id=execution_id,
            event_type=EventTypes.AGENT_TOOL_CALL,
            data={
                "node_name": node_config.get("name", "unknown"),
                "tool_name": tool_name,
                "tool_args": tool_args_dict,
            }
        )

        result = _execute_tool_with_retries(tool_func, tool_args, tool_exec_retries)

        result_str = str(result)
        result_preview = result_str[:1000] + "..." if len(result_str) > 1000 else result_str

        register_event(
            backends=backends,
            execution_id=execution_id,
            event_type=EventTypes.AGENT_TOOL_RESULT,
            data={
                "node_name": node_config.get("name", "unknown"),
                "tool_name": tool_name,
                "result_preview": result_preview,
                "result_length": len(result_str),
            }
        )

        loop_state.add_tool_response(tool_name, result)

    except Exception as e:
        loop_state.add_tool_error(tool_name, str(e))

    return True


def _execute_tool_with_retries(
    tool_func: Callable,
    tool_args: Any,
    max_retries: int,
) -> Any:
    """Execute a tool with retry logic."""
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return tool_func(**tool_args.model_dump())
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue

    if last_error:
        raise last_error
