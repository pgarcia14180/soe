"""Local file-based workflow backend - dumb storage only."""

import json
from pathlib import Path
from typing import Dict, Any


class LocalWorkflowBackend:
    """File-based workflow storage backend."""

    def __init__(self, storage_dir: str = "./orchestration_data/workflows"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_workflows_registry(
        self, execution_id: str, workflows_registry: Dict[str, Any]
    ) -> None:
        """Save workflows registry for execution ID."""
        workflows_file = self.storage_dir / f"{execution_id}_workflows.json"

        with open(workflows_file, "w") as f:
            json.dump(workflows_registry, f, indent=2, default=str)

    def soe_get_workflows_registry(self, execution_id: str) -> Dict[str, Any]:
        """Get workflows registry for execution ID."""
        workflows_file = self.storage_dir / f"{execution_id}_workflows.json"

        if not workflows_file.exists():
            return {}

        with open(workflows_file, "r") as f:
            return json.load(f)

    def save_current_workflow_name(self, execution_id: str, workflow_name: str) -> None:
        """Save current workflow name for execution ID."""
        current_workflow_file = self.storage_dir / f"{execution_id}_current.txt"

        with open(current_workflow_file, "w") as f:
            f.write(workflow_name)

    def get_current_workflow_name(self, execution_id: str) -> str:
        """Get current workflow name for execution ID."""
        current_workflow_file = self.storage_dir / f"{execution_id}_current.txt"

        if not current_workflow_file.exists():
            return ""

        with open(current_workflow_file, "r") as f:
            return f.read().strip()

    def cleanup_all(self) -> None:
        """Delete all workflow files. Used for test cleanup."""
        for workflow_file in self.storage_dir.glob("*_workflows.json"):
            workflow_file.unlink()
        for current_file in self.storage_dir.glob("*_current.txt"):
            current_file.unlink()
