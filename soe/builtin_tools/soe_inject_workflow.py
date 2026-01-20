"""Built-in workflow injection tool."""

import json
from typing import Dict, Any, Callable
from ..types import EventTypes
from ..lib.register_event import register_event
from ..lib.yaml_parser import parse_yaml


def create_soe_inject_workflow_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_inject_workflow tool with workflow access

    Args:
        execution_id: ID to access workflow data via backends
        backends: Backend services to fetch/update workflows
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_inject_workflow function that can inject new workflows
    """

    def soe_inject_workflow(workflow_name: str, workflow_data: str) -> Dict[str, Any]:
        """
        Built-in tool: Inject a new workflow into the global workflows configuration

        Args:
            workflow_name: Name of the new workflow to inject
            workflow_data: JSON or YAML string containing the workflow definition

        Returns:
            Success confirmation with injected workflow info
        """

        # Parse the workflow definition (prefer JSON, fallback to YAML)
        parsed_workflow = None

        try:
            parsed_workflow = json.loads(workflow_data)
        except json.JSONDecodeError:
            parsed_workflow = parse_yaml(workflow_data)

        if not isinstance(parsed_workflow, dict):
            raise ValueError("Workflow data must be a dictionary/object")

        # Determine the workflow definition to inject
        workflow_definition = None

        # If workflow_name is specified in the parsed data, use that specific workflow
        if workflow_name in parsed_workflow:
            workflow_definition = parsed_workflow[workflow_name]
        else:
            # Check if all keys in parsed_workflow look like node names (have node_type)
            all_nodes = True
            for _, value in parsed_workflow.items():
                if not isinstance(value, dict) or "node_type" not in value:
                    all_nodes = False
                    break

            if all_nodes:
                # All top-level keys are nodes, use the entire structure as the workflow
                workflow_definition = parsed_workflow
            elif len(parsed_workflow) == 1:
                # Single non-node entry, assume it's a workflow container
                first_workflow_key = list(parsed_workflow.keys())[0]
                workflow_definition = parsed_workflow[first_workflow_key]
            else:
                # Multiple entries, assume entire structure is the workflow
                workflow_definition = parsed_workflow

        if not workflow_definition:
            raise ValueError(f"No workflow definition found for injection")

        # Validate the workflow before injecting
        from ..validation.config import validate_workflow
        validate_workflow(workflow_name, workflow_definition)

        # Get current workflows registry via backends and inject new workflow
        workflows_registry = backends.workflow.get_workflows_registry(execution_id)
        workflows_registry[workflow_name] = workflow_definition

        # Save the updated workflows registry back
        backends.workflow.save_workflows_registry(execution_id, workflows_registry)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_inject_workflow",
                "workflow_name": workflow_name,
            },
        )

        return {
            "injected": True,
            "workflow_name": workflow_name,
            "message": f"Successfully injected workflow '{workflow_name}'",
        }

    return soe_inject_workflow
