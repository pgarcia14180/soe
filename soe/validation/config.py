"""
Config validation - validates config structure before orchestration starts.

Supports two config formats:
1. Single Workflow format: Dict of workflow definitions directly
2. Combined config format: Dict with 'workflows', 'context_schema', 'identities' keys

Runs once at orchestration start, before any execution.
"""

from typing import Dict, Any

from ..types import WorkflowValidationError
from ..nodes.router.validation import validate_node_config as validate_router
from ..nodes.agent.validation import validate_node_config as validate_agent
from ..nodes.llm.validation import validate_node_config as validate_llm
from ..nodes.child.validation import validate_node_config as validate_child
from ..nodes.tool.validation import validate_node_config as validate_tool
from ..lib.yaml_parser import parse_yaml


NODE_VALIDATORS = {
    "router": validate_router,
    "agent": validate_agent,
    "llm": validate_llm,
    "child": validate_child,
    "tool": validate_tool,
}


def _validate_workflow_section(workflow_name: str, workflow: Dict[str, Any]) -> None:
    """
    Validate all nodes in a workflow section.

    Args:
        workflow_name: Name of the workflow (for error messages)
        workflow: Workflow definition dict

    Raises:
        WorkflowValidationError: If any node configuration is invalid
    """
    if not workflow:
        raise WorkflowValidationError(
            f"Workflow '{workflow_name}' is empty - at least one node is required"
        )

    for node_name, node_config in workflow.items():
        if node_name.startswith("__"):
            raise WorkflowValidationError(
                f"Workflow '{workflow_name}': node name '{node_name}' is reserved - "
                f"names starting with '__' are reserved for internal use"
            )
        node_type = node_config.get("node_type")

        if not node_type:
            raise WorkflowValidationError(
                f"Workflow '{workflow_name}', node '{node_name}': "
                f"'node_type' is required - specify the type (router, agent, llm, tool, child)"
            )

        if node_type.startswith("_"):
            continue

        validator = NODE_VALIDATORS.get(node_type)
        if not validator:
            valid_types = ", ".join(NODE_VALIDATORS.keys())
            raise WorkflowValidationError(
                f"Workflow '{workflow_name}', node '{node_name}': "
                f"unknown node_type '{node_type}'. Valid types are: {valid_types}"
            )

        try:
            validator(node_config)
        except WorkflowValidationError as e:
            raise WorkflowValidationError(
                f"Workflow '{workflow_name}', node '{node_name}': {e}"
            ) from e


def _validate_context_schema_section(context_schema: Dict[str, Any]) -> None:
    """
    Validate context_schema section of config.

    Args:
        context_schema: Context schema definitions

    Raises:
        WorkflowValidationError: If schema format is invalid
    """
    if not isinstance(context_schema, dict):
        raise WorkflowValidationError(
            "'context_schema' section must be an object mapping field names to schemas"
        )

    for field_name, field_schema in context_schema.items():
        if not isinstance(field_schema, (dict, str)):
            raise WorkflowValidationError(
                f"context_schema.{field_name}: schema must be an object or type string"
            )


def _validate_identities_section(identities: Dict[str, str]) -> None:
    """
    Validate identities section of config.

    Args:
        identities: Identity definitions (name -> system prompt)

    Raises:
        WorkflowValidationError: If identity format is invalid
    """
    if not isinstance(identities, dict):
        raise WorkflowValidationError(
            "'identities' section must be an object mapping identity names to prompts"
        )

    for identity_name, identity_prompt in identities.items():
        if not isinstance(identity_prompt, str):
            raise WorkflowValidationError(
                f"identities.{identity_name}: identity prompt must be a string, "
                f"got {type(identity_prompt).__name__}"
            )


def validate_config(config) -> Dict[str, Any]:
    """
    Parse and validate config.

    Supports two formats:
    1. Legacy format: Dict of workflow definitions directly
    2. Combined config format: Dict with 'workflows', 'context_schema', 'identities' keys

    Args:
        config: YAML string or dict (workflows only or combined config)

    Returns:
        Parsed config dict (either workflows directly or combined structure)

    Raises:
        WorkflowValidationError: If any configuration is invalid
    """
    parsed = parse_yaml(config)

    if "workflows" in parsed:
        workflows = parsed["workflows"]
        if not isinstance(workflows, dict):
            raise WorkflowValidationError(
                "'workflows' section must be an object containing workflow definitions"
            )
        for workflow_name, workflow in workflows.items():
            if not isinstance(workflow, dict):
                raise WorkflowValidationError(
                    f"Workflow '{workflow_name}' must be an object containing node definitions"
                )
            _validate_workflow_section(workflow_name, workflow)

        context_schema = parsed.get("context_schema")
        if context_schema is not None:
            _validate_context_schema_section(context_schema)

        identities = parsed.get("identities")
        if identities is not None:
            _validate_identities_section(identities)
    else:
        for workflow_name, workflow in parsed.items():
            if not isinstance(workflow, dict):
                raise WorkflowValidationError(
                    f"Workflow '{workflow_name}' must be an object containing node definitions"
                )
            _validate_workflow_section(workflow_name, workflow)

    return parsed


validate_workflow = _validate_workflow_section


def validate_orchestrate_params(
    initial_workflow_name: str,
    initial_signals: list,
) -> None:
    """Validate orchestrate() parameters before execution starts."""
    if not isinstance(initial_signals, list):
        raise WorkflowValidationError(
            f"'initial_signals' must be a list, got {type(initial_signals).__name__}. "
            f"Example: initial_signals=['START']"
        )
    if not initial_signals:
        raise WorkflowValidationError(
            "'initial_signals' cannot be empty - at least one signal is required to start execution"
        )
    if not isinstance(initial_workflow_name, str) or not initial_workflow_name:
        raise WorkflowValidationError(
            "'initial_workflow_name' must be a non-empty string"
        )
