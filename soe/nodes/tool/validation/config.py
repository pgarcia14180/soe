"""
Tool node configuration validation.

Called once at orchestration start, not during node execution.
"""

from typing import Dict, Any, Callable, Union

from ....types import WorkflowValidationError
from ....builtin_tools import get_builtin_tool_factory
from ..types import ToolRegistryEntry, ToolsRegistry


def _get_function_from_entry(entry: Union[Callable, ToolRegistryEntry]) -> Callable:
    """Extract the callable from a registry entry"""
    if callable(entry):
        return entry
    return entry.get("function")


def _validate_registry_entry(tool_name: str, entry: Union[Callable, ToolRegistryEntry]) -> None:
    """
    Validate a tool registry entry format.

    Raises:
        WorkflowValidationError: If entry format is invalid
    """
    if callable(entry):
        return

    if not isinstance(entry, dict):
        raise WorkflowValidationError(
            f"Tool '{tool_name}' registry entry must be a callable or dict with 'function' key"
        )

    if "function" not in entry:
        raise WorkflowValidationError(
            f"Tool '{tool_name}' registry entry dict must have 'function' key"
        )

    if not callable(entry["function"]):
        raise WorkflowValidationError(
            f"Tool '{tool_name}' 'function' must be callable"
        )

    max_retries = entry.get("max_retries")
    if max_retries is not None:
        if not isinstance(max_retries, int) or max_retries < 0:
            raise WorkflowValidationError(
                f"Tool '{tool_name}' 'max_retries' must be a non-negative integer"
            )

    failure_signal = entry.get("failure_signal")
    if failure_signal is not None:
        if not isinstance(failure_signal, str):
            raise WorkflowValidationError(
                f"Tool '{tool_name}' 'failure_signal' must be a string"
            )


def validate_node_config(node_config: Dict[str, Any]) -> None:
    """
    Validate tool node configuration (structure only, no runtime checks).
    Called once at orchestration start, not during node execution.

    Raises:
        WorkflowValidationError: If configuration is invalid
    """
    event_triggers = node_config.get("event_triggers")
    if not event_triggers:
        raise WorkflowValidationError(
            "'event_triggers' is required - specify which signals activate this tool node"
        )
    if not isinstance(event_triggers, list):
        raise WorkflowValidationError(
            "'event_triggers' must be a list, e.g., [\"EXECUTE_TOOL\"]"
        )

    if "tool_name" not in node_config:
        raise WorkflowValidationError(
            "'tool_name' is required - specify which tool to execute"
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
                    f"'event_emissions[{i}]' must be a dict with 'signal_name'"
                )
            if "signal_name" not in emission:
                raise WorkflowValidationError(
                    f"'event_emissions[{i}]' must have 'signal_name'"
                )

    output_field = node_config.get("output_field")
    if output_field is not None:
        if not isinstance(output_field, str):
            raise WorkflowValidationError(
                "'output_field' must be a string - the context field name to store the tool output"
            )
        if output_field == "__operational__":
            raise WorkflowValidationError(
                "'output_field' cannot be '__operational__' - this is a reserved system field"
            )


def validate_tool_node_config(
    node_config: Dict[str, Any], tools_registry: ToolsRegistry
) -> None:
    """Validate tool node configuration with runtime checks (tool registry)"""

    validate_node_config(node_config)

    tool_name = node_config["tool_name"]
    if tool_name not in tools_registry:
        if not get_builtin_tool_factory(tool_name):
            raise WorkflowValidationError(
                f"Tool '{tool_name}' not found in tools_registry or builtin tools"
            )
        return

    entry = tools_registry[tool_name]
    _validate_registry_entry(tool_name, entry)

    tool_function = _get_function_from_entry(entry)
    if not callable(tool_function):
        raise WorkflowValidationError(f"Tool '{tool_name}' is not callable")
