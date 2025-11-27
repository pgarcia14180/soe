"""
Signal extraction helpers for tests.
"""

from typing import List


def extract_signals(backends, execution_id) -> List[str]:
    """
    Extract broadcast signals from context's __operational__.signals.

    This reads signals directly from the execution's context, which includes
    all signals broadcast during that execution.

    For tests involving child workflows, use extract_signals on the parent
    execution_id - signals propagated via signals_to_parent will appear
    in the parent's __operational__.signals.

    Args:
        backends: LocalBackends instance
        execution_id: The execution ID to query

    Returns:
        List of signal names that were broadcast during execution
    """
    context = backends.context.get_context(execution_id)
    operational = context.get("__operational__", {})
    return operational.get("signals", [])


def extract_signals_from_telemetry(backends, execution_id) -> List[str]:
    """
    Extract broadcast signals from telemetry events (legacy approach).

    Prefer extract_signals() which reads from __operational__.signals.
    This function is kept for backwards compatibility and debugging.

    Args:
        backends: LocalBackends instance with telemetry
        execution_id: The execution ID to query

    Returns:
        List of signal names that were broadcast during execution
    """
    telemetry_events = backends.telemetry.get_events(execution_id)
    signals = []
    for event in telemetry_events:
        if event.get("event_type") == "signals_broadcast":
            signals.extend(event.get("context", {}).get("signals", []))
    return signals
