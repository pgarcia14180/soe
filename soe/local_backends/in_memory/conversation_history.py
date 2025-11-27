"""
In-memory conversation history backend
"""

from typing import Dict, Any, List


class InMemoryConversationHistoryBackend:
    """In-memory conversation history backend"""

    def __init__(self):
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def get_conversation_history(self, identity: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for identity

        Args:
            identity: User/Agent identity

        Returns:
            List of conversation messages
        """
        return self._history.get(identity, [])

    def append_to_conversation_history(self, identity: str, entry: Dict[str, Any]) -> None:
        """
        Append entry to conversation history

        Args:
            identity: User/Agent identity
            entry: Message entry to append
        """
        if identity not in self._history:
            self._history[identity] = []
        self._history[identity].append(entry)

    def save_conversation_history(self, identity: str, history: List[Dict[str, Any]]) -> None:
        """
        Save full conversation history

        Args:
            identity: User/Agent identity
            history: Full history list
        """
        self._history[identity] = history

    def delete_conversation_history(self, identity: str) -> None:
        """
        Delete conversation history for identity

        Args:
            identity: User/Agent identity
        """
        if identity in self._history:
            del self._history[identity]

    def cleanup_all(self) -> None:
        """Cleanup all data"""
        self._history.clear()
