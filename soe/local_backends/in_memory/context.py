"""
In-memory context backend
"""

from typing import Dict, Any


class InMemoryContextBackend:
    """In-memory context storage backend"""

    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}

    def get_context(self, execution_id: str) -> Dict[str, Any]:
        """
        Get context for execution ID

        Args:
            execution_id: Unique execution identifier

        Returns:
            Context dictionary, empty if not found
        """
        return self._storage.get(execution_id, {})

    def save_context(self, execution_id: str, context: Dict[str, Any]) -> None:
        """
        Save context for execution ID

        Args:
            execution_id: Unique execution identifier
            context: Context dictionary to save
        """
        self._storage[execution_id] = context.copy()

    def cleanup_all(self) -> None:
        """Cleanup all data"""
        self._storage.clear()
