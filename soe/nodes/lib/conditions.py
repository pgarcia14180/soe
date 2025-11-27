"""
Shared condition evaluation for nodes that emit signals.
Used by Router, LLM, Agent, and Tool nodes.
"""

import re
from typing import Dict, List, Any
from jinja2 import Environment


def _create_accumulated_filter(full_context: Dict[str, Any]):
    """Create an accumulated filter that returns full history for a field."""
    def accumulated_filter(value):
        """
        Return the full accumulated history list for a context field.

        If history has exactly one entry and it's a list, returns that list
        (common case: initial context passed a list as value).
        Otherwise returns the history entries.
        """
        for key, hist_list in full_context.items():
            if key.startswith("__"):
                continue
            if isinstance(hist_list, list) and hist_list and hist_list[-1] == value:
                if len(hist_list) == 1 and isinstance(hist_list[0], list):
                    return hist_list[0]
                return hist_list
        return [value] if value is not None else []

    return accumulated_filter


def evaluate_conditions(
    event_emissions: List[Dict[str, Any]],
    render_context: Dict[str, Any],
    full_context: Dict[str, Any] = None,
) -> List[str]:
    """
    Evaluate jinja conditions and return signals that pass.

    Args:
        event_emissions: List of emission configs with signal_name and optional condition
        render_context: Variables for jinja (e.g., {"context": ctx} or {"result": res, "context": ctx})
        full_context: The raw context with history lists (for accumulated filter)

    Returns:
        List of signal names that passed their conditions (or had no condition)
    """
    jinja_env = Environment()

    if full_context:
        jinja_env.filters["accumulated"] = _create_accumulated_filter(full_context)

    filtered_signals = []

    for emission in event_emissions:
        signal_name = emission.get("signal_name")
        condition = emission.get("condition", "")

        if not condition or not re.search(r"\{\{.*\}\}", condition):
            filtered_signals.append(signal_name)
            continue

        try:
            result = jinja_env.from_string(condition).render(**render_context)
            if result and result.strip().lower() not in ["false", "0", "none", ""]:
                filtered_signals.append(signal_name)
        except Exception:
            pass

    return filtered_signals
