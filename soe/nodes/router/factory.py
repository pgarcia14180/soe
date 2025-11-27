"""
Router node factory
"""

from typing import Dict, Any

from ..lib.conditions import evaluate_conditions
from ...lib.context_fields import get_field
from ...validation.operational import validate_operational
from ...lib.register_event import register_event
from ...local_backends import EventTypes
from ...types import BroadcastSignalsCaller, RouterNodeCaller
from .validation import validate_node_config
from .state import get_operational_state


def create_router_node_caller(
    backends, broadcast_signals_caller: BroadcastSignalsCaller
) -> RouterNodeCaller:
    """Create router node caller with pre-loaded dependencies."""

    def execute_router_node(id: str, node_config: Dict[str, Any]) -> None:
        validate_operational(id, backends)
        validate_node_config(node_config)

        state = get_operational_state(id, node_config, backends)

        register_event(backends, id, EventTypes.NODE_EXECUTION, {"node_type": "router"})

        unwrapped = {k: get_field(state.context, k) for k in state.context if not k.startswith("__")}
        for k, v in state.context.items():
            if k.startswith("__"):
                unwrapped[k] = v
        signals = evaluate_conditions(state.event_emissions, {"context": unwrapped}, state.context)
        if signals:
            broadcast_signals_caller(id, signals)

    return execute_router_node
