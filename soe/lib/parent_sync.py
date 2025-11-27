"""
Parent sync utilities for sub-orchestration.

These functions check if a signal or context update should be propagated
to the parent workflow based on the injected __parent__ metadata.
"""

from typing import Dict, Any, Tuple, Optional, List
from ..types import Backends

PARENT_INFO_KEY = "__parent__"


def get_signals_for_parent(
    signals: List[str], context: Dict[str, Any]
) -> Tuple[Optional[str], List[str]]:
    """Get the subset of signals that should be propagated to the parent."""
    parent_info = context.get(PARENT_INFO_KEY)
    if not parent_info:
        return (None, [])

    parent_execution_id = parent_info.get("parent_execution_id")
    signals_to_parent = set(parent_info.get("signals_to_parent", []))
    matching_signals = [s for s in signals if s in signals_to_parent]

    return (parent_execution_id, matching_signals)


def _check_parent_context_sync(
    key: str, context: Dict[str, Any]
) -> Tuple[Optional[str], bool]:
    """Determine if a context update should be propagated to the parent."""
    parent_info = context.get(PARENT_INFO_KEY)
    if not parent_info:
        return (None, False)

    parent_execution_id = parent_info.get("parent_execution_id")
    context_updates_to_parent = parent_info.get("context_updates_to_parent", [])

    if key in context_updates_to_parent:
        return (parent_execution_id, True)

    return (parent_execution_id, False)


def sync_context_to_parent(
    context: Dict[str, Any],
    updated_keys: List[str],
    backends: Backends,
) -> None:
    """Sync updated context keys to the parent workflow if configured.

    For each key in updated_keys that is configured for parent sync:
    - If parent doesn't have the key, copy the full list from child
    - If parent already has the key, extend with new items from child
    """
    for key in updated_keys:
        parent_id, should_sync = _check_parent_context_sync(key, context)
        if should_sync and parent_id:
            parent_context = backends.context.get_context(parent_id)
            child_history = context[key]

            if key in parent_context:
                # Append new items from child to parent's existing list
                parent_context[key].extend(child_history)
            else:
                # Initialize parent with child's history
                parent_context[key] = child_history

            backends.context.save_context(parent_id, parent_context)
            sync_context_to_parent(parent_context, [key], backends)
