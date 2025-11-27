"""
Router node configuration validation.

Called once at orchestration start, not during node execution.
"""

from typing import Dict, Any
from ....types import WorkflowValidationError
from ....validation.jinja import validate_jinja_syntax


def validate_node_config(node_config: Dict[str, Any]) -> None:
    """
    Validate router node configuration exhaustively.
    Called once at orchestration start, not during node execution.

    Raises:
        WorkflowValidationError: If configuration is invalid
    """
    event_triggers = node_config.get("event_triggers")
    if not event_triggers:
        raise WorkflowValidationError(
            "'event_triggers' is required - specify which signals activate this router"
        )
    if not isinstance(event_triggers, list):
        raise WorkflowValidationError(
            "'event_triggers' must be a list, e.g., [\"START\", \"RETRY\"]"
        )

    event_emissions = node_config.get("event_emissions")
    if not event_emissions:
        raise WorkflowValidationError(
            "'event_emissions' is required - specify which signals to emit based on conditions"
        )
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
        if condition:
            validate_jinja_syntax(
                condition,
                f"Event emission '{emission.get('signal_name')}' condition"
            )
