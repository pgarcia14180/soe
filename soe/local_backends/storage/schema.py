"""
Context schema backend for workflow context field validation.

Stores and retrieves schemas that define the structure of workflow context fields.
Keyed by execution_id (main_execution_id) so children can access parent's schemas.
Dumb storage only - no validation logic (see soe/lib/schema_validation.py).
"""

from typing import Dict, Any, Optional
import os
import yaml

from ...lib.yaml_parser import parse_yaml


class LocalContextSchemaBackend:
    """
    Local file-based context schema storage backend.

    Stores context schemas as YAML files keyed by execution_id.
    """

    def __init__(self, storage_dir: str = "./orchestration_data/schemas"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_schema_path(self, execution_id: str) -> str:
        """Get file path for an execution's context schema."""
        return os.path.join(self.storage_dir, f"{execution_id}.yaml")

    def save_context_schema(self, execution_id: str, schema: Dict[str, Any]) -> None:
        """
        Save a context schema for an execution.

        Args:
            execution_id: Execution ID (typically main_execution_id)
            schema: Schema definition dict
        """
        path = self._get_schema_path(execution_id)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(schema, f, default_flow_style=False)
        self._cache[execution_id] = schema

    def get_context_schema(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context schema for an execution.

        Args:
            execution_id: Execution ID (typically main_execution_id)

        Returns:
            Schema dict or None if not found
        """
        # Check cache first
        if execution_id in self._cache:
            return self._cache[execution_id]

        # Load from file
        path = self._get_schema_path(execution_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                schema = parse_yaml(f.read())
            self._cache[execution_id] = schema
            return schema

        return None

    def delete_context_schema(self, execution_id: str) -> bool:
        """
        Delete an execution's context schema.

        Args:
            execution_id: Execution ID (typically main_execution_id)

        Returns:
            True if deleted, False if not found
        """
        path = self._get_schema_path(execution_id)
        if os.path.exists(path):
            os.remove(path)
            self._cache.pop(execution_id, None)
            return True
        return False

    def cleanup_all(self) -> None:
        """
        Remove all stored context schemas.

        This method is useful for test cleanup to remove all stored data.
        """
        import shutil
        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)
            os.makedirs(self.storage_dir, exist_ok=True)
        self._cache.clear()
