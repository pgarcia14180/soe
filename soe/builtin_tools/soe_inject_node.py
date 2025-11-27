"""Built-in node configuration injection tool."""

import json
from typing import Dict, Any, Callable
from ..local_backends import EventTypes
from ..lib.register_event import register_event
from ..lib.yaml_parser import parse_yaml


def create_soe_inject_node_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_inject_node tool with workflow access

    Args:
        execution_id: ID to access workflow data via backends
        backends: Backend services to fetch/update workflows
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_inject_node function that can inject node config into workflows
    """

    def soe_soe_inject_node(
        workflow_name: str, node_name: str, node_config_data: str
    ) -> Dict[str, Any]:
        """
        Built-in tool: Inject a node configuration into an existing workflow

        Args:
            workflow_name: Name of the workflow to modify
            node_name: Name of the node to inject
            node_config_data: YAML or JSON string containing the node configuration

        Returns:
            Success confirmation with injected node info
        """

        # Get current workflows registry and validate workflow exists
        workflows_registry = backends.workflow.soe_get_workflows_registry(execution_id)

        if workflow_name not in workflows_registry:
            raise ValueError(
                f"Workflow '{workflow_name}' not found in workflows registry"
            )

        # Parse the node configuration data (prefer JSON, fallback to YAML)
        node_config = None

        try:
            node_config = json.loads(node_config_data)
        except json.JSONDecodeError:
            node_config = parse_yaml(node_config_data)

        if not isinstance(node_config, dict):
            raise ValueError("Node configuration must be a dictionary/object")

        # Inject the node configuration into the workflow
        target_workflow = workflows_registry[workflow_name]
        target_workflow[node_name] = node_config

        # Save the updated workflows registry back
        backends.workflow.save_workflows_registry(execution_id, workflows_registry)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_inject_node",
                "workflow_name": workflow_name,
                "node_name": node_name,
            },
        )

        return {
            "injected": True,
            "workflow_name": workflow_name,
            "node_name": node_name,
            "message": f"Successfully injected node '{node_name}' into workflow '{workflow_name}'",
        }

    return soe_soe_inject_node
