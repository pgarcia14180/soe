"""Built-in workflow removal tool."""

from typing import Dict, Any, Callable
from ..types import EventTypes
from ..lib.register_event import register_event


def create_soe_remove_workflow_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_remove_workflow tool with workflow access

    Args:
        execution_id: ID to access workflow data via backends
        backends: Backend services to fetch/update workflows
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_remove_workflow function that can remove workflows
    """

    def soe_remove_workflow(workflow_name: str) -> Dict[str, Any]:
        """
        Built-in tool: Remove a workflow from the global workflows configuration

        Args:
            workflow_name: Name of the workflow to remove

        Returns:
            Success confirmation with removed workflow info
        """
        workflows_registry = backends.workflow.get_workflows_registry(execution_id)

        if workflow_name not in workflows_registry:
            raise ValueError(
                f"Workflow '{workflow_name}' not found in workflows registry"
            )

        del workflows_registry[workflow_name]

        backends.workflow.save_workflows_registry(execution_id, workflows_registry)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_remove_workflow",
                "workflow_name": workflow_name,
            },
        )

        return {
            "removed": True,
            "workflow_name": workflow_name,
            "message": f"Successfully removed workflow '{workflow_name}'",
        }

    return soe_remove_workflow
