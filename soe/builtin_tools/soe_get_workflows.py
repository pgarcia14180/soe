"""Built-in workflow retrieval tool."""

from typing import Dict, Any, Callable, Optional, List


def create_soe_get_workflows_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_get_workflows tool.

    Args:
        execution_id: ID to access workflow data via backends
        backends: Backend services to fetch workflows
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_get_workflows function
    """

    def soe_get_workflows(
        workflow_name: Optional[str] = None,
        list_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Get workflow information from the current registry.

        Args:
            workflow_name: If provided, get only this specific workflow's nodes.
                          If None, returns info about all workflows.
            list_only: If True, only return workflow names (not full node configs).
                      Default is False for backward compatibility.

        Returns:
            If list_only=True: {"workflow_names": ["orchestrator", "ecosystem", ...]}
            If workflow_name provided: {"workflow_name": "...", "nodes": {...}}
            Otherwise: Full dict of workflow_name -> node_configs

        Example usage:
            soe_get_workflows(list_only=True)  # Just get workflow names
            soe_get_workflows(workflow_name="orchestrator")  # Get specific workflow
            soe_get_workflows()  # Get everything (legacy behavior)
        """
        registry = backends.workflow.soe_get_workflows_registry(execution_id)

        if list_only:
            return {"workflow_names": list(registry.keys())}

        if workflow_name:
            if workflow_name in registry:
                return {
                    "workflow_name": workflow_name,
                    "nodes": list(registry[workflow_name].keys()),
                    "node_configs": registry[workflow_name],
                }
            else:
                return {"error": f"Workflow '{workflow_name}' not found", "available": list(registry.keys())}

        return registry

    return soe_get_workflows
