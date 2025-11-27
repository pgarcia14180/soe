"""
Child node configuration validation.

Called once at orchestration start, not during node execution.
"""

from typing import Dict, Any
from ....types import WorkflowValidationError


def validate_node_config(node_config: Dict[str, Any]) -> None:
    """
    Validate sub-orchestration node configuration exhaustively.
    Called once at orchestration start, not during node execution.

    Raises:
        WorkflowValidationError: If configuration is invalid
    """
    child_workflow_name = node_config.get("child_workflow_name")
    if not child_workflow_name:
        raise WorkflowValidationError(
            "'child_workflow_name' is required - specify which workflow to start as a child"
        )
    if not isinstance(child_workflow_name, str):
        raise WorkflowValidationError(
            "'child_workflow_name' must be a string"
        )

    child_initial_signals = node_config.get("child_initial_signals")
    if not child_initial_signals:
        raise WorkflowValidationError(
            "'child_initial_signals' is required - specify which signals to start the child workflow with"
        )
    if not isinstance(child_initial_signals, list):
        raise WorkflowValidationError(
            "'child_initial_signals' must be a list of signal names"
        )

    event_triggers = node_config.get("event_triggers")
    if not event_triggers:
        raise WorkflowValidationError(
            "'event_triggers' is required - specify which signals trigger the start of the child workflow"
        )
    if not isinstance(event_triggers, list):
        raise WorkflowValidationError(
            "'event_triggers' must be a list of signal names, e.g., [\"START_CHILD\"]"
        )

    signals_to_parent = node_config.get("signals_to_parent")
    if signals_to_parent is not None:
        if not isinstance(signals_to_parent, list):
            raise WorkflowValidationError(
                "'signals_to_parent' must be a list of signal names that should propagate from child to parent"
            )
        for signal in signals_to_parent:
            if not isinstance(signal, str):
                raise WorkflowValidationError(
                    f"All items in 'signals_to_parent' must be strings. Found: {type(signal).__name__}"
                )

    context_updates_to_parent = node_config.get("context_updates_to_parent")
    if context_updates_to_parent is not None:
        if not isinstance(context_updates_to_parent, list):
            raise WorkflowValidationError(
                "'context_updates_to_parent' must be a list of context key names that should propagate from child to parent"
            )
        for key in context_updates_to_parent:
            if not isinstance(key, str):
                raise WorkflowValidationError(
                    f"All items in 'context_updates_to_parent' must be strings. Found: {type(key).__name__}"
                )

    input_fields = node_config.get("input_fields")
    if input_fields is not None and not isinstance(input_fields, list):
        raise WorkflowValidationError(
            "'input_fields' must be a list of context field names to pass to the child workflow"
        )

    fan_out_field = node_config.get("fan_out_field")
    if fan_out_field is not None:
        if not isinstance(fan_out_field, str):
            raise WorkflowValidationError(
                "'fan_out_field' must be a string (the context field to iterate over)"
            )
        child_input_field = node_config.get("child_input_field")
        if not child_input_field:
            raise WorkflowValidationError(
                "'child_input_field' is required when 'fan_out_field' is set - "
                "specify which field in child context receives each item"
            )
        if not isinstance(child_input_field, str):
            raise WorkflowValidationError(
                "'child_input_field' must be a string"
            )

    spawn_interval = node_config.get("spawn_interval")
    if spawn_interval is not None:
        if not isinstance(spawn_interval, (int, float)):
            raise WorkflowValidationError(
                "'spawn_interval' must be a number (seconds to sleep between spawns)"
            )
        if spawn_interval < 0:
            raise WorkflowValidationError(
                "'spawn_interval' must be non-negative"
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
