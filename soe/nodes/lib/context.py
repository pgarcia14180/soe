"""Context output utilities shared across nodes."""

from typing import Any, Optional
from ...lib.parent_sync import sync_context_to_parent
from ...lib.context_fields import set_field, get_field
from ...types import Backends

__all__ = ["set_field", "get_field", "save_output_to_context"]


def save_output_to_context(
    execution_id: str,
    output_field: Optional[str],
    output_value: Any,
    backends: Backends,
) -> None:
    """Save output value to context and sync to parent if configured."""
    if not output_field or output_value is None:
        return

    context = backends.context.get_context(execution_id)
    set_field(context, output_field, output_value)
    backends.context.save_context(execution_id, context)
    sync_context_to_parent(context, [output_field], backends)
