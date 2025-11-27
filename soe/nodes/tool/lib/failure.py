"""Tool failure handling utilities."""

from typing import Optional

from ...lib.context import save_output_to_context
from ....lib.register_event import register_event
from ....local_backends import EventTypes
from ....types import Backends, BroadcastSignalsCaller


def handle_tool_failure(
    tool_name: str,
    failure_signal: Optional[str],
    output_field: Optional[str],
    error_message: str,
    backends: Backends,
    broadcast_signals_caller: BroadcastSignalsCaller,
    execution_id: str,
) -> None:
    """Handle tool execution failure by saving error and optionally emitting failure signal."""
    save_output_to_context(execution_id, output_field, error_message, backends)

    register_event(
        backends, execution_id, EventTypes.NODE_ERROR,
        {"tool_name": tool_name, "error": error_message}
    )

    if failure_signal:
        broadcast_signals_caller(execution_id, [failure_signal])
