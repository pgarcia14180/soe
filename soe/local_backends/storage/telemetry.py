"""
Local file-based telemetry backend - dumb storage only.
"""

import json
from pathlib import Path
from typing import Dict, Any
from ...types import EventTypes


class LocalTelemetryBackend:
    """File-based telemetry storage backend"""

    def __init__(self, storage_dir: str = "./orchestration_data/telemetry"):
        """
        Initialize local telemetry backend

        Args:
            storage_dir: Directory to store telemetry files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def log_event(self, execution_id: str, event_type: str, **event_data) -> None:
        """
        Log an event for an execution ID

        Args:
            execution_id: Unique execution identifier
            event_type: Type of event (use EventTypes constants)
            **event_data: Additional event-specific data (caller provides timestamp)
        """
        event = {
            "event_type": event_type,
            **event_data,
        }

        telemetry_file = self.storage_dir / f"{execution_id}.jsonl"

        with open(telemetry_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def get_events(self, execution_id: str) -> list[Dict[str, Any]]:
        """
        Get all events for execution ID

        Args:
            execution_id: Unique execution identifier

        Returns:
            List of event dictionaries, empty if not found
        """
        telemetry_file = self.storage_dir / f"{execution_id}.jsonl"

        if not telemetry_file.exists():
            return []

        events = []
        with open(telemetry_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events

    def cleanup_all(self) -> None:
        """Delete all telemetry files. Used for test cleanup."""
        for telemetry_file in self.storage_dir.glob("*.jsonl"):
            telemetry_file.unlink()
