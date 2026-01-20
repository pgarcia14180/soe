"""
Unified event registration for telemetry and operational state.

Records events to telemetry backend and updates operational context state
(signals, nodes, llm_calls, tool_calls, errors).
"""

from datetime import datetime
from typing import Dict, Any, Optional
from ..types import Backends, EventTypes


def register_event(
    backends: Backends,
    execution_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log telemetry and update operational state based on event type.

    Args:
        backends: Backend services
        execution_id: The execution ID
        event_type: Event type from EventTypes enum
        data: Event-specific data
    """
    data = data or {}

    # Log to telemetry if available
    if backends.telemetry is not None:
        backends.telemetry.log_event(
            execution_id,
            event_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            context=data
        )

    # Update operational state based on event type

    if event_type == EventTypes.SIGNALS_BROADCAST:
        context = backends.context.get_context(execution_id)
        operational = context["__operational__"]
        signals = data.get("signals", [])
        operational["signals"].extend(signals)
        backends.context.save_context(execution_id, context)

    elif event_type == EventTypes.NODE_EXECUTION:
        node_name = data.get("node_name")
        if node_name:
            context = backends.context.get_context(execution_id)
            operational = context["__operational__"]
            nodes = operational["nodes"]
            if node_name not in nodes:
                nodes[node_name] = 0
            nodes[node_name] += 1
            backends.context.save_context(execution_id, context)

    elif event_type == EventTypes.LLM_CALL:
        context = backends.context.get_context(execution_id)
        operational = context["__operational__"]
        operational["llm_calls"] += 1
        backends.context.save_context(execution_id, context)

    elif event_type == EventTypes.NODE_ERROR:
        context = backends.context.get_context(execution_id)
        operational = context["__operational__"]
        operational["errors"] += 1
        backends.context.save_context(execution_id, context)

    elif event_type in (EventTypes.TOOL_CALL, EventTypes.AGENT_TOOL_CALL):
        context = backends.context.get_context(execution_id)
        operational = context["__operational__"]
        operational["tool_calls"] += 1
        backends.context.save_context(execution_id, context)
