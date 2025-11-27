"""In-memory context schema backend - dumb storage only.

Keyed by execution_id (main_execution_id) so children can access parent's schemas.
"""

from typing import Dict, Any, Optional


class InMemoryContextSchemaBackend:
    """In-memory context schema backend."""

    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def save_context_schema(self, execution_id: str, schema: Dict[str, Any]) -> None:
        """Save context schema for execution."""
        self._schemas[execution_id] = schema

    def get_context_schema(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get context schema for execution."""
        return self._schemas.get(execution_id)

    def delete_context_schema(self, execution_id: str) -> bool:
        """
        Delete context schema for execution.

        Args:
            execution_id: Execution ID (typically main_execution_id)

        Returns:
            True if deleted, False if not found
        """
        if execution_id in self._schemas:
            del self._schemas[execution_id]
            return True
        return False

    def cleanup_all(self) -> None:
        """Cleanup all data"""
        self._schemas.clear()
