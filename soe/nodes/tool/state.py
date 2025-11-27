"""
Tool node state retrieval.
"""

from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

from ...types import Backends
from ...lib.yaml_parser import parse_yaml
from ...lib.context_fields import get_field
from ..lib.tools import get_tool_from_registry
from .types import ToolsRegistry


class ToolOperationalState(BaseModel):
    """All data needed for tool node execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: Dict[str, Any]
    main_execution_id: str
    tool_name: str
    tool_function: Callable
    max_retries: int
    failure_signal: Optional[str]
    output_field: Optional[str]
    event_emissions: List[Dict[str, Any]]
    parameters: Any  # Can be Dict or List when process_accumulated=True
    process_accumulated: bool = False


def get_operational_state(
    execution_id: str,
    node_config: Dict[str, Any],
    backends: Backends,
    tools_registry: ToolsRegistry,
) -> ToolOperationalState:
    """Retrieve all state needed for tool node execution."""
    context = backends.context.get_context(execution_id)
    operational = context["__operational__"]
    tool_name = node_config["tool_name"]
    tool_function, max_retries, failure_signal, process_accumulated = get_tool_from_registry(
        tool_name, tools_registry, execution_id, backends
    )

    context_parameter_field = node_config.get("context_parameter_field")
    if context_parameter_field and context_parameter_field in context:
        if process_accumulated:
            raw_params = context[context_parameter_field]
        else:
            raw_params = get_field(context, context_parameter_field)
        parameters = parse_yaml(raw_params) if isinstance(raw_params, str) else raw_params
    else:
        parameters = {}

    return ToolOperationalState(
        context=context,
        main_execution_id=operational["main_execution_id"],
        tool_name=tool_name,
        tool_function=tool_function,
        max_retries=max_retries,
        failure_signal=failure_signal,
        output_field=node_config.get("output_field"),
        event_emissions=node_config.get("event_emissions", []),
        parameters=parameters,
        process_accumulated=process_accumulated,
    )
