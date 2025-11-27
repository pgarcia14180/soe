"""Built-in tool to add a signal to a node's event emissions."""

from typing import Dict, Any, Callable
from ..local_backends import EventTypes
from ..lib.register_event import register_event


def create_soe_add_signal_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create add_signal tool.
    """

    def add_signal(
        workflow_name: str, node_name: str, signal_name: str, condition: str
    ) -> Dict[str, Any]:
        """
        Add a signal to a node's event_emissions list.

        Args:
            workflow_name: Name of the workflow
            node_name: Name of the node
            signal_name: Name of the signal to add
            condition: Jinja condition for the signal

        Returns:
            Success confirmation
        """
        workflows_registry = backends.workflow.soe_get_workflows_registry(execution_id)

        if workflow_name not in workflows_registry:
            raise ValueError(f"Workflow '{workflow_name}' not found")

        workflow = workflows_registry[workflow_name]
        if node_name not in workflow:
            raise ValueError(f"Node '{node_name}' not found in workflow '{workflow_name}'")

        node_config = workflow[node_name]

        if "event_emissions" not in node_config:
            node_config["event_emissions"] = []

        # Check if signal already exists
        for emission in node_config["event_emissions"]:
            if emission.get("signal_name") == signal_name:
                # Update existing
                emission["condition"] = condition
                backends.workflow.save_workflows_registry(execution_id, workflows_registry)
                return {
                    "status": "updated",
                    "message": f"Updated signal '{signal_name}' in node '{node_name}'"
                }

        # Add new signal
        node_config["event_emissions"].append({
            "signal_name": signal_name,
            "condition": condition
        })

        backends.workflow.save_workflows_registry(execution_id, workflows_registry)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "add_signal",
                "workflow_name": workflow_name,
                "node_name": node_name,
                "signal": signal_name
            },
        )

        return {
            "status": "added",
            "message": f"Added signal '{signal_name}' to node '{node_name}'"
        }

    return add_signal
