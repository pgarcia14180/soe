"""Built-in node removal tool."""

from typing import Dict, Any, Callable
from ..local_backends import EventTypes
from ..lib.register_event import register_event


def create_soe_remove_node_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_remove_node tool with workflow access

    Args:
        execution_id: ID to access workflow data via backends
        backends: Backend services to fetch/update workflows
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_remove_node function that can remove nodes from workflows
    """

    def soe_remove_node(workflow_name: str, node_name: str) -> Dict[str, Any]:
        """
        Built-in tool: Remove a node from an existing workflow

        Args:
            workflow_name: Name of the workflow to modify
            node_name: Name of the node to remove

        Returns:
            Success confirmation with removed node info
        """
        workflows_registry = backends.workflow.soe_get_workflows_registry(execution_id)

        if workflow_name not in workflows_registry:
            raise ValueError(
                f"Workflow '{workflow_name}' not found in workflows registry"
            )

        target_workflow = workflows_registry[workflow_name]

        if node_name not in target_workflow:
            raise ValueError(
                f"Node '{node_name}' not found in workflow '{workflow_name}'"
            )

        del target_workflow[node_name]

        backends.workflow.save_workflows_registry(execution_id, workflows_registry)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_remove_node",
                "workflow_name": workflow_name,
                "node_name": node_name,
            },
        )

        return {
            "removed": True,
            "workflow_name": workflow_name,
            "node_name": node_name,
            "message": f"Successfully removed node '{node_name}' from workflow '{workflow_name}'",
        }

    return soe_remove_node
