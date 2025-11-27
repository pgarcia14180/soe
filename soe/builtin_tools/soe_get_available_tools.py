"""Built-in tool to list available tools."""

from typing import Dict, Any, Callable, List


def create_soe_get_available_tools_tool(
    execution_id: str,
    backends,
    tools_registry: Dict[str, Any] = None,
) -> Callable:
    """
    Factory function to create soe_get_available_tools tool.

    Args:
        execution_id: ID for the execution
        backends: Backend services
        tools_registry: Registry of user-provided tools

    Returns:
        Configured soe_get_available_tools function
    """
    from . import BUILTIN_TOOLS

    def soe_get_available_tools() -> Dict[str, List[str]]:
        """
        Get all available tools that can be used in workflows.

        Returns:
            {
                "builtin_tools": [...list of builtin tool names...],
                "user_tools": [...list of user-provided tool names...]
            }
        """
        builtin_names = list(BUILTIN_TOOLS.keys())
        user_names = list(tools_registry.keys()) if tools_registry else []

        return {
            "builtin_tools": builtin_names,
            "user_tools": user_names,
        }

    return soe_get_available_tools
