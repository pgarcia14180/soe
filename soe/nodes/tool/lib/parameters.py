"""Tool parameter extraction and validation utilities."""

import inspect
from typing import Dict, Any, Callable, Optional

from ....lib.context_fields import get_field
from ..types import ToolParameterError


def extract_tool_parameters(
    context: Dict[str, Any],
    context_parameter_field: Optional[str],
) -> Dict[str, Any]:
    """Extract tool parameters from context.

    Args:
        context: The workflow context
        context_parameter_field: Name of the context field containing tool kwargs

    Returns:
        Dict of parameters to pass to the tool function

    Raises:
        ToolParameterError: If field is missing or not a dict
    """
    if not context_parameter_field:
        return {}

    if context_parameter_field not in context:
        raise ToolParameterError(f"Context missing required field: {context_parameter_field}")

    parameters = get_field(context, context_parameter_field)

    if not isinstance(parameters, dict):
        raise ToolParameterError(
            f"Context field '{context_parameter_field}' must be a dict of parameters, got {type(parameters)}"
        )

    return parameters


def validate_tool_parameters(
    tool_function: Callable, parameters: Dict[str, Any], tool_name: str
) -> None:
    """Validate parameters match tool function signature."""
    signature = inspect.signature(tool_function)

    has_var_keyword = any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    )

    for param_name, param in signature.parameters.items():
        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            continue
        if param.default == inspect.Parameter.empty:
            if param_name not in parameters:
                raise ToolParameterError(
                    f"Tool '{tool_name}' missing required parameter: {param_name}"
                )

    if not has_var_keyword:
        for param_name in parameters.keys():
            if param_name not in signature.parameters:
                raise ToolParameterError(
                    f"Tool '{tool_name}' unexpected parameter: {param_name}"
                )
