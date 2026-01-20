"""
Shared LLM output utilities for LLM and Agent nodes.
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel

from .signals import has_jinja_conditions
from ...lib.schema_validation import schema_to_root_model
from ...lib.register_event import register_event
from ...types import EventTypes


def needs_llm_signal_selection(event_emissions: List[Dict[str, Any]]) -> bool:
    """Check if LLM should select which signal to emit."""
    if not event_emissions:
        return False
    if has_jinja_conditions(event_emissions):
        return False

    signal_count = sum(1 for e in event_emissions if e.get("signal_name"))
    return signal_count > 1


def get_signal_options(event_emissions: List[Dict[str, Any]]) -> Optional[List[Dict[str, str]]]:
    """
    Get signal options if LLM should select which signal to emit.

    Returns list of {name, description} dicts if multiple signals available.
    Uses 'condition' field as description (when it's plain text, not jinja).
    Returns None if no selection needed (single signal, jinja conditions, or empty).
    """
    if needs_llm_signal_selection(event_emissions):
        return [
            {
                "name": e.get("signal_name"),
                "description": e.get("condition", ""),
            }
            for e in event_emissions
            if e.get("signal_name")
        ]
    return None


def get_output_model(
    backends,
    main_execution_id: str,
    output_field: Optional[str]
) -> Optional[Type[BaseModel]]:
    """Get RootModel for flat output validation if schema exists."""
    if not output_field or not backends.context_schema:
        return None

    schema = backends.context_schema.get_context_schema(main_execution_id)
    if not schema or output_field not in schema:
        register_event(
            backends,
            main_execution_id,
            EventTypes.CONTEXT_WARNING,
            {
                "message": f"Output field '{output_field}' not found in context schema",
                "output_field": output_field,
            },
        )
        return None

    field_def = schema.get(output_field)
    return schema_to_root_model(field_def, f"{output_field.title()}Root")
