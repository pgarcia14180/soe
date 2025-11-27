"""In-memory identity backend - dumb storage only.

Keyed by execution_id (main_execution_id) so children can access parent's identities.

Identity format is simple: identity_name -> system_prompt (string)
Example:
    assistant: "You are a helpful assistant."
    coding_expert: "You are an expert programmer."
"""

from typing import Dict, Optional


class InMemoryIdentityBackend:
    """In-memory identity backend.

    Stores identity definitions per execution. Identities define the
    participating personas/roles and are used as initial system prompts.
    """

    def __init__(self):
        self._identities: Dict[str, Dict[str, str]] = {}

    def save_identities(self, execution_id: str, identities: Dict[str, str]) -> None:
        """Save identity definitions for execution."""
        self._identities[execution_id] = identities

    def get_identities(self, execution_id: str) -> Optional[Dict[str, str]]:
        """Get identity definitions for execution."""
        return self._identities.get(execution_id)

    def get_identity(self, execution_id: str, identity_name: str) -> Optional[str]:
        """Get a specific identity's system prompt."""
        identities = self.get_identities(execution_id)
        if identities and identity_name in identities:
            return identities[identity_name]
        return None

    def delete_identities(self, execution_id: str) -> bool:
        """Delete identity definitions for execution.

        Returns:
            True if deleted, False if not found
        """
        if execution_id in self._identities:
            del self._identities[execution_id]
            return True
        return False

    def cleanup_all(self) -> None:
        """Cleanup all data."""
        self._identities.clear()
