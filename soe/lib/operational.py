"""
Operational context initialization.

This module handles initialization of the operational state structure.
Runtime updates are handled by register_event.py.
"""

from typing import Dict, Any

PARENT_INFO_KEY = "__parent__"


def wrap_context_fields(context: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap context field values in lists for history tracking.

    Internal fields (starting with __) are not wrapped.
    If context has __parent__, fields are already wrapped (from parent workflow).
    """
    # Child workflows receive pre-wrapped fields from parent
    if PARENT_INFO_KEY in context:
        return context

    return {
        k: [v] if not k.startswith("__") else v
        for k, v in context.items()
    }


def add_operational_state(
    execution_id: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Add operational state to context if not present. Returns new context dict."""
    if "__operational__" in context:
        return context

    parent_info = context.get(PARENT_INFO_KEY, {})
    inherited_main_id = parent_info.get("main_execution_id")
    main_id = inherited_main_id if inherited_main_id else execution_id

    return {
        **context,
        "__operational__": {
            "signals": [],
            "nodes": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "main_execution_id": main_id
        }
    }
