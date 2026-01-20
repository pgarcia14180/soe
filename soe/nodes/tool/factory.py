"""
Tool node factory
"""

from typing import Dict, Any

from .validation import validate_tool_node_config
from .validation.operational import validate_tool_node_runtime
from .state import get_operational_state
from .lib.failure import handle_tool_failure
from .lib.conditions import evaluate_tool_conditions
from .types import ToolsRegistry
from ...lib.register_event import register_event
from ..lib.context import save_output_to_context
from ...types import Backends, BroadcastSignalsCaller, ToolNodeCaller, EventTypes


def create_tool_node_caller(
    backends: Backends,
    tools_registry: ToolsRegistry,
    broadcast_signals_caller: BroadcastSignalsCaller,
) -> ToolNodeCaller:
    """Create tool node caller with pre-loaded dependencies."""

    def execute_tool_node(id: str, node_config: Dict[str, Any]) -> None:
        validate_tool_node_config(node_config, tools_registry)
        validate_tool_node_runtime(id, backends)

        state = get_operational_state(id, node_config, backends, tools_registry)

        register_event(
            backends, id, EventTypes.TOOL_CALL,
            {"tool_name": state.tool_name, "max_retries": state.max_retries}
        )

        last_error = None
        for attempt in range(state.max_retries + 1):
            try:
                if state.process_accumulated and isinstance(state.parameters, list):
                    result = state.tool_function(state.parameters)
                else:
                    result = state.tool_function(**state.parameters)
                save_output_to_context(id, state.output_field, result, backends)

                signals = evaluate_tool_conditions(
                    state.event_emissions, result, state.context, id, backends
                )
                if signals:
                    broadcast_signals_caller(id, signals)
                return

            except Exception as tool_error:
                last_error = tool_error
                if attempt < state.max_retries:
                    register_event(
                        backends, id, EventTypes.NODE_ERROR,
                        {"tool_name": state.tool_name, "retry_attempt": attempt + 1, "error": str(tool_error)}
                    )
                    continue

        handle_tool_failure(
            state.tool_name, state.failure_signal, state.output_field,
            str(last_error), backends, broadcast_signals_caller, id
        )

    return execute_tool_node
