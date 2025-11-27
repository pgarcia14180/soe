"""
Shared signal emission utilities for LLM-based nodes.

Provides common logic for emitting signals after node completion,
handling both LLM-selected signals and jinja-conditioned emissions.
"""

from typing import Dict, List, Any, Optional, Protocol

from ...types import BroadcastSignalsCaller, Backends
from ...lib.register_event import register_event
from ...local_backends import EventTypes
from .signals import has_jinja_conditions, handle_signal_emission


class OperationalState(Protocol):
    """Protocol for operational state objects that can emit signals."""
    context: Dict[str, Any]
    event_emissions: List[Dict[str, Any]]


def handle_llm_failure(
    failure_signal: Optional[str],
    error_message: str,
    node_type: str,
    execution_id: str,
    backends: Backends,
    broadcast_signals_caller: BroadcastSignalsCaller,
) -> None:
    """Handle LLM/Agent node failure by logging and emitting failure signal or raising."""
    register_event(
        backends, execution_id, EventTypes.NODE_ERROR,
        {"node_type": node_type, "error": error_message}
    )

    if failure_signal:
        broadcast_signals_caller(execution_id, [failure_signal])
    else:
        raise RuntimeError(error_message)


def emit_completion_signals(
    selected_signal: Optional[str],
    node_config: Dict[str, Any],
    operational_state: OperationalState,
    broadcast_signals_caller: BroadcastSignalsCaller,
    execution_id: str,
) -> None:
    """
    Emit signals after successful node completion.

    Signal emission priority:
    1. LLM-selected signal (when multiple signals with plain-text conditions)
    2. Jinja-conditioned emissions (evaluate {{ }} templates)
    3. Single unconditional signal (emit it)
    4. Multiple signals without selection → error (shouldn't happen)

    The 'condition' field has dual purpose:
    - Plain text: used as description for LLM signal selection
    - Jinja template ({{ }}): evaluated to determine if signal should emit
    """
    if selected_signal:
        broadcast_signals_caller(execution_id, [selected_signal])
    elif operational_state.event_emissions:
        if has_jinja_conditions(operational_state.event_emissions):
            handle_signal_emission(
                [], node_config, operational_state.context,
                broadcast_signals_caller, execution_id
            )
        else:
            signals = [
                e.get("signal_name") for e in operational_state.event_emissions
                if e.get("signal_name")
            ]
            if len(signals) == 1:
                broadcast_signals_caller(execution_id, signals)
            elif len(signals) > 1:
                raise RuntimeError(
                    f"Multiple signals defined but no selection made: {signals}"
                )
