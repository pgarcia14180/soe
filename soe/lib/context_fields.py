"""
Context field utilities for history-aware field storage.

Fields are stored as lists to maintain update history.
Reading always returns the last (most recent) value.
"""

from typing import Any, Dict, List


def set_field(context: Dict[str, Any], field: str, value: Any) -> None:
    """Set a context field, appending to history list."""
    if field.startswith("__"):
        context[field] = value
        return

    if field not in context:
        context[field] = [value]
    else:
        context[field].append(value)


def get_field(context: Dict[str, Any], field: str) -> Any:
    """Get a context field value (last item in history list)."""
    if field.startswith("__"):
        return context.get(field)

    value = context.get(field)
    if value is None:
        return None

    return value[-1]


def get_accumulated(context: Dict[str, Any], field: str) -> List[Any]:
    """
    Get full accumulated history for a field.

    If history has exactly one entry and it's a list, returns that list
    (common case: initial context passed a list as value for fan-out).
    """
    if field not in context:
        return []

    history = context[field]

    # If history has exactly one entry and it's a list, return that list
    if len(history) == 1 and isinstance(history[0], list):
        return list(history[0])

    return list(history)
