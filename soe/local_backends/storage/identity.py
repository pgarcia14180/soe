"""
Identity backend for workflow identity definitions.

Stores and retrieves identities that define the participating personas/roles
in a workflow. These are used as initial system prompts for conversation history.
Keyed by execution_id (main_execution_id) so children can access parent's identities.
Dumb storage only - no validation logic.

Identity format is simple: identity_name -> system_prompt (string)
Example:
    assistant: "You are a helpful assistant."
    coding_expert: "You are an expert programmer."
"""

from typing import Dict, Optional
import os
import yaml

from ...lib.yaml_parser import parse_yaml


class LocalIdentityBackend:
    """
    Local file-based identity storage backend.

    Stores identity definitions as YAML files keyed by execution_id.
    """

    def __init__(self, storage_dir: str = "./orchestration_data/identities"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, str]] = {}

    def _get_identity_path(self, execution_id: str) -> str:
        """Get file path for an execution's identities."""
        return os.path.join(self.storage_dir, f"{execution_id}.yaml")

    def save_identities(self, execution_id: str, identities: Dict[str, str]) -> None:
        """
        Save identity definitions for an execution.

        Args:
            execution_id: Execution ID (typically main_execution_id)
            identities: Identity definitions (identity_name -> system_prompt)
        """
        path = self._get_identity_path(execution_id)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(identities, f, default_flow_style=False)
        self._cache[execution_id] = identities

    def get_identities(self, execution_id: str) -> Optional[Dict[str, str]]:
        """
        Get identity definitions for an execution.

        Args:
            execution_id: Execution ID (typically main_execution_id)

        Returns:
            Identity definitions dict (identity_name -> system_prompt) or None if not found
        """
        if execution_id in self._cache:
            return self._cache[execution_id]

        path = self._get_identity_path(execution_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                identities = parse_yaml(f.read())
            self._cache[execution_id] = identities
            return identities

        return None

    def get_identity(self, execution_id: str, identity_name: str) -> Optional[str]:
        """
        Get a specific identity's system prompt.

        Args:
            execution_id: Execution ID (typically main_execution_id)
            identity_name: Name of the identity

        Returns:
            System prompt string or None if not found
        """
        identities = self.get_identities(execution_id)
        if identities and identity_name in identities:
            return identities[identity_name]
        return None

    def delete_identities(self, execution_id: str) -> bool:
        """
        Delete an execution's identity definitions.

        Args:
            execution_id: Execution ID (typically main_execution_id)

        Returns:
            True if deleted, False if not found
        """
        path = self._get_identity_path(execution_id)
        deleted = False

        if execution_id in self._cache:
            del self._cache[execution_id]
            deleted = True

        if os.path.exists(path):
            os.remove(path)
            deleted = True

        return deleted

    def cleanup_all(self) -> None:
        """Cleanup all stored data."""
        self._cache.clear()
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".yaml"):
                    os.remove(os.path.join(self.storage_dir, filename))
