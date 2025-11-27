"""
Tool node models and exceptions
"""

from typing import Callable, TypedDict, Union, Dict


class ToolRegistryEntry(TypedDict, total=False):
    """Extended tool registry entry with optional configuration"""
    function: Callable
    max_retries: int
    failure_signal: str


ToolsRegistry = Dict[str, Union[Callable, ToolRegistryEntry]]


class ToolNodeConfigurationError(Exception):
    """Raised when tool node configuration is invalid"""

    pass


class ToolParameterError(Exception):
    """Raised when tool parameters don't match signature"""

    pass
