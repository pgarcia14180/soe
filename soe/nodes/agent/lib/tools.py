"""
Agent node tool loading utilities.
"""

from typing import Dict, Any, List

from ...lib.tools import get_tool_signature, get_tool_from_registry


def load_tools_and_build_signatures(
    tool_names: List[str],
    tools_registry: Dict[str, Dict[str, Any]],
    execution_id: str,
    backends,
) -> str:
    """Load tools and build signature string for agent prompt.

    Args:
        tool_names: List of tool names to load
        tools_registry: Dict mapping tool name -> {function: callable, max_retries: int}
        execution_id: Current workflow execution ID
        backends: Backend services

    Returns:
        Formatted string with all tool signatures for the prompt
    """
    tools_info = []

    for tool_name in tool_names:
        tool_func, _, _, _ = get_tool_from_registry(
            tool_name, tools_registry, execution_id, backends
        )
        tools_info.append(get_tool_signature(tool_func))

    return "\n\n".join(tools_info) if tools_info else ""
