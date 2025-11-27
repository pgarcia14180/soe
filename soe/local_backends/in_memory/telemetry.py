"""
In-memory telemetry backend - dumb storage only.
"""

from typing import Dict, Any, List


class InMemoryTelemetryBackend:
    """In-memory telemetry backend"""

    def __init__(self):
        self._events: Dict[str, List[Dict[str, Any]]] = {}

    def log_event(self, execution_id: str, event_type: str, **event_data) -> None:
        """
        Log telemetry event

        Args:
            execution_id: Execution ID
            event_type: Type of event
            **event_data: Additional event data
        """
        if execution_id not in self._events:
            self._events[execution_id] = []

        event = {
            "event_type": event_type,
            **event_data
        }
        self._events[execution_id].append(event)

    def get_events(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get all events for an execution ID"""
        return self._events.get(execution_id, [])

    def cleanup_all(self) -> None:
        """Cleanup all data"""
        self._events.clear()
