"""
Local file-based conversation history backend

This backend stores conversation history by identity, allowing agents
to persist their conversation state across different node executions.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


class LocalConversationHistoryBackend:
    """File-based conversation history storage backend"""

    def __init__(self, storage_dir: str = "./orchestration_data/conversations"):
        """
        Initialize local conversation history backend

        Args:
            storage_dir: Directory to store conversation history files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get_conversation_history(self, identity: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for an identity

        Args:
            identity: Unique identity identifier for the agent

        Returns:
            List of conversation entries, empty if not found
        """
        history_file = self.storage_dir / f"{identity}.json"

        if not history_file.exists():
            return []

        with open(history_file, "r") as f:
            return json.load(f)

    def append_to_conversation_history(
        self, identity: str, entry: Dict[str, Any]
    ) -> None:
        """
        Append a single entry to the conversation history

        Args:
            identity: Unique identity identifier for the agent
            entry: Conversation entry to append
        """
        history = self.get_conversation_history(identity)
        history.append(entry)
        self.save_conversation_history(identity, history)

    def save_conversation_history(
        self, identity: str, history: List[Dict[str, Any]]
    ) -> None:
        """
        Save full conversation history for an identity

        Args:
            identity: Unique identity identifier for the agent
            history: Full conversation history list to save
        """
        history_file = self.storage_dir / f"{identity}.json"

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2, default=str)

    def delete_conversation_history(self, identity: str) -> None:
        """Delete conversation history for an identity."""
        history_file = self.storage_dir / f"{identity}.json"
        if history_file.exists():
            history_file.unlink()

    def cleanup_all(self) -> None:
        """Delete all conversation history files. Used for test cleanup."""
        for history_file in self.storage_dir.glob("*.json"):
            history_file.unlink()
