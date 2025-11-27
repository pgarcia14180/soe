"""
Signal handling utilities for LLM-based nodes.
"""

import re
from typing import Dict, List, Any, Callable

from .conditions import evaluate_conditions
from ...lib.context_fields import get_field


def has_jinja_conditions(event_emissions: List[Dict[str, Any]]) -> bool:
    """Check if any event emission has jinja template conditions."""
    return any(
        e.get("condition") and re.search(r"\{\{.*\}\}", e.get("condition", ""))
        for e in event_emissions
    )


def _evaluate_emission_conditions(
    emitted_signals: List[str], node_config: Dict[str, Any], context: Dict[str, Any]
) -> List[str]:
    """Evaluate jinja conditions and filter signals against allowed emissions."""
    event_emissions = node_config.get("event_emissions", [])

    has_jinja = any(
        e.get("condition") and re.search(r"\{\{.*\}\}", e.get("condition", ""))
        for e in event_emissions
    )

    if not has_jinja:
        allowed = {e.get("signal_name") for e in event_emissions if e.get("signal_name")}
        return [s for s in emitted_signals if s in allowed]

    unwrapped = {k: get_field(context, k) for k in context if not k.startswith("__")}
    for k, v in context.items():
        if k.startswith("__"):
            unwrapped[k] = v
    return evaluate_conditions(event_emissions, {"context": unwrapped}, context)


def handle_signal_emission(
    emitted_signals: List[str],
    node_config: Dict[str, Any],
    context: Dict[str, Any],
    broadcast_signals_caller: Callable[[str, List[str]], None],
    execution_id: str,
) -> None:
    """Evaluate signal conditions and emit via broadcast_signals_caller."""
    filtered_signals = _evaluate_emission_conditions(
        emitted_signals, node_config, context
    )
    if filtered_signals:
        broadcast_signals_caller(execution_id, filtered_signals)
