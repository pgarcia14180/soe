"""
Local file-based context backend
"""

import json
from pathlib import Path
from typing import Dict, Any


class LocalContextBackend:
    """File-based context storage backend"""

    def __init__(self, storage_dir: str = "./orchestration_data/contexts"):
        """
        Initialize local context backend

        Args:
            storage_dir: Directory to store context files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get_context(self, execution_id: str) -> Dict[str, Any]:
        """
        Get context for execution ID

        Args:
            execution_id: Unique execution identifier

        Returns:
            Context dictionary, empty if not found
        """
        context_file = self.storage_dir / f"{execution_id}.json"

        if not context_file.exists():
            return {}

        with open(context_file, "r") as f:
            return json.load(f)

    def save_context(self, execution_id: str, context: Dict[str, Any]) -> None:
        """
        Save context for execution ID

        Args:
            execution_id: Unique execution identifier
            context: Context dictionary to save
        """
        context_file = self.storage_dir / f"{execution_id}.json"

        with open(context_file, "w") as f:
            json.dump(context, f, indent=2, default=str)

    def cleanup_all(self) -> None:
        """Delete all context files. Used for test cleanup."""
        for context_file in self.storage_dir.glob("*.json"):
            context_file.unlink()
