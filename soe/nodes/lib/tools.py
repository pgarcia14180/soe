"""
Shared tool utilities for nodes that work with callable tools.

Used by Agent node and Tool node for introspection and registry lookup.
"""

import inspect
from typing import Dict, Any, Callable, Type, Optional, Union
from pydantic import BaseModel, create_model

from ...types import Backends
from ...builtin_tools import get_builtin_tool_factory


DEFAULT_MAX_RETRIES = 0


def get_tool_signature(tool_func: Callable) -> str:
    """Extract function signature and docstring for prompt."""
    sig = inspect.signature(tool_func)
    params = []
    for name, param in sig.parameters.items():
        param_type = (
            param.annotation if param.annotation != inspect.Parameter.empty else "Any"
        )
        params.append(f"{name}: {param_type}")

    func_name = tool_func.__name__
    params_str = ", ".join(params)
    doc = inspect.getdoc(tool_func) or "No description"

    return f"{func_name}({params_str})\n  {doc}"


def create_tool_schema(tool_func: Callable) -> Type[BaseModel]:
    """Dynamically create a Pydantic model from a function signature."""
    sig = inspect.signature(tool_func)
    fields: Dict[str, Any] = {}

    for name, param in sig.parameters.items():
        annotation = param.annotation
        if annotation == inspect.Parameter.empty:
            annotation = Any

        default = param.default
        if default == inspect.Parameter.empty:
            field_info = (annotation, ...)
        else:
            field_info = (annotation, default)

        fields[name] = field_info

    return create_model(f"{tool_func.__name__}Schema", **fields)


def _normalize_registry_entry(
    entry: Union[Callable, Dict[str, Any]],
) -> tuple[Callable, int, Optional[str], bool]:
    """Normalize a tool registry entry to extract function and configuration."""
    if callable(entry):
        return entry, DEFAULT_MAX_RETRIES, None, False

    return (
        entry["function"],
        entry.get("max_retries", DEFAULT_MAX_RETRIES),
        entry.get("failure_signal"),
        entry.get("process_accumulated", False),
    )


def get_tool_from_registry(
    tool_name: str,
    tools_registry: Dict[str, Any],
    execution_id: str,
    backends: Backends,
) -> tuple[Callable, int, Optional[str], bool]:
    """
    Get tool function from registry or builtin tools, normalizing the entry.

    Caches builtin tools in registry after creation.

    Returns:
        Tuple of (tool_function, max_retries, failure_signal, process_accumulated)
    """
    entry = tools_registry.get(tool_name)

    if entry is not None:
        return _normalize_registry_entry(entry)

    builtin_factory = get_builtin_tool_factory(tool_name)
    if builtin_factory:
        tool_function = builtin_factory(
            execution_id=execution_id,
            backends=backends,
            tools_registry=tools_registry,
        )
        tools_registry[tool_name] = {"function": tool_function, "max_retries": DEFAULT_MAX_RETRIES}
        return tool_function, DEFAULT_MAX_RETRIES, None, False

    raise ValueError(f"Tool '{tool_name}' not found in registry or builtins")
