"""
Tool-specific condition evaluation with error logging.
"""

from typing import Dict, List, Any

from ...lib.conditions import evaluate_conditions
from ....lib.context_fields import get_field
from ....lib.register_event import register_event
from ....types import Backends, EventTypes


def evaluate_tool_conditions(
    event_emissions: List[Dict[str, Any]],
    result: Any,
    context: Dict[str, Any],
    execution_id: str,
    backends: Backends,
) -> List[str]:
    """Evaluate jinja conditions against tool result and context with error logging."""
    if not event_emissions:
        return []

    try:
        unwrapped = {k: get_field(context, k) for k in context if not k.startswith("__")}
        for k, v in context.items():
            if k.startswith("__"):
                unwrapped[k] = v
        return evaluate_conditions(event_emissions, {"result": result, "context": unwrapped}, context)
    except Exception as e:
        register_event(
            backends, execution_id, EventTypes.NODE_ERROR,
            {"error": f"Condition evaluation failed: {e}"}
        )
        return []
