"""In-memory workflow backend - dumb storage only."""

from typing import Dict, Any
import copy


class InMemoryWorkflowBackend:
    """In-memory workflow storage backend."""

    def __init__(self):
        self._registries: Dict[str, Any] = {}
        self._current_workflows: Dict[str, str] = {}

    def save_workflows_registry(self, id: str, workflows: Dict[str, Any]) -> None:
        """Save workflows registry for execution ID."""
        self._registries[id] = copy.deepcopy(workflows)

    def get_workflows_registry(self, id: str) -> Any:
        """Get workflows registry for execution ID."""
        return copy.deepcopy(self._registries.get(id))

    def save_current_workflow_name(self, id: str, name: str) -> None:
        """Save current workflow name for execution ID."""
        self._current_workflows[id] = name

    def get_current_workflow_name(self, id: str) -> str:
        """Get current workflow name for execution ID."""
        return self._current_workflows.get(id, "")

    def cleanup_all(self) -> None:
        """Cleanup all data."""
        self._registries.clear()
        self._current_workflows.clear()
