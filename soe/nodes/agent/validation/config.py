"""
Agent node configuration validation.

Called once at orchestration start, not during node execution.
"""

from typing import Dict, Any, List
from ....types import WorkflowValidationError


def validate_node_config(node_config: Dict[str, Any]) -> None:
    """
    Validate agent node configuration exhaustively.
    Called once at orchestration start, not during node execution.

    Raises:
        WorkflowValidationError: If configuration is invalid
    """
    event_triggers = node_config.get("event_triggers")
    if not event_triggers:
        raise WorkflowValidationError(
            "'event_triggers' is required - specify which signals activate this agent"
        )
    if not isinstance(event_triggers, list):
        raise WorkflowValidationError(
            "'event_triggers' must be a list, e.g., [\"START\", \"RETRY\"]"
        )

    if not node_config.get("prompt"):
        raise WorkflowValidationError(
            "'prompt' is required - provide the agent's task description or instructions"
        )

    if node_config.get("input_fields") is not None:
        raise WorkflowValidationError(
            "'input_fields' is no longer supported for Agent nodes. "
            "Use Jinja syntax in prompts instead: {{ context.field_name }}"
        )

    output_field = node_config.get("output_field")
    if output_field is not None:
        if not isinstance(output_field, str):
            raise WorkflowValidationError(
                "'output_field' must be a string - the context field name to store the agent's output"
            )
        if output_field == "__operational__":
            raise WorkflowValidationError(
                "'output_field' cannot be '__operational__' - this is a reserved system field"
            )

    retries = node_config.get("retries")
    if retries is not None:
        if not isinstance(retries, int) or retries < 0:
            raise WorkflowValidationError(
                "'retries' must be a positive integer (default is 3)"
            )

    event_emissions = node_config.get("event_emissions")
    if event_emissions is not None:
        if not isinstance(event_emissions, list):
            raise WorkflowValidationError(
                "'event_emissions' must be a list of signal definitions"
            )
        for i, emission in enumerate(event_emissions):
            if not isinstance(emission, dict):
                raise WorkflowValidationError(
                    f"Each event_emission must be an object with 'signal_name', got invalid item at position {i + 1}"
                )
            if not emission.get("signal_name"):
                raise WorkflowValidationError(
                    f"Event emission at position {i + 1} is missing 'signal_name'"
                )
            condition = emission.get("condition")
            if condition is not None and not isinstance(condition, str):
                raise WorkflowValidationError(
                    f"Event emission at position {i + 1} has invalid 'condition' - must be a jinja string"
                )

    tools = node_config.get("tools")
    if tools is not None and not isinstance(tools, list):
        raise WorkflowValidationError(
            "'tools' must be a list of tool names available to the agent"
        )

    identity = node_config.get("identity")
    if identity is not None and not isinstance(identity, str):
        raise WorkflowValidationError(
            "'identity' must be a string - used to persist conversation history across executions"
        )

    llm_failure_signal = node_config.get("llm_failure_signal")
    if llm_failure_signal is not None and not isinstance(llm_failure_signal, str):
        raise WorkflowValidationError(
            "'llm_failure_signal' must be a string - the signal to emit when LLM call fails"
        )
