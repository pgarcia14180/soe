"""
Built-in dynamic tool invocation.

Allows LLMs to call any registered tool by name at runtime.
This enables meta-level tool orchestration.
"""

import json
from typing import Dict, Any, Callable
from ..local_backends import EventTypes
from ..lib.register_event import register_event


def create_soe_call_tool_tool(
    execution_id: str,
    backends,
    tools_registry: dict,
) -> Callable:
    """
    Factory function to create call_tool with access to tools registry.

    Args:
        execution_id: Current execution ID
        backends: Backend services
        tools_registry: Registry of available tools {name: {"function": callable, ...}}

    Returns:
        Configured call_tool function
    """

    def call_tool(tool_name: str, arguments: str = "{}") -> Dict[str, Any]:
        """
        Dynamically invoke a registered tool by name.

        This is a meta-tool that allows calling any other tool at runtime.
        Useful for dynamic workflows where the tool to call is determined
        by context or user input.

        Args:
            tool_name: Name of the tool to invoke (must be registered)
            arguments: JSON string of arguments to pass to the tool

        Returns:
            The result from the invoked tool, or an error dict

        Example:
            call_tool("get_secret", '{"key": "password"}')
            call_tool("write_file", '{"path": "test.txt", "content": "hello"}')
        """
        # Parse arguments
        try:
            args = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError as e:
            return {
                "error": f"Invalid JSON arguments: {e}",
                "tool_name": tool_name,
            }

        # Check if tool exists
        if tool_name not in tools_registry:
            available = list(tools_registry.keys())
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": available[:20],  # Limit to avoid huge responses
            }

        # Get tool function
        tool_entry = tools_registry[tool_name]
        if isinstance(tool_entry, dict):
            tool_func = tool_entry.get("function")
        elif callable(tool_entry):
            tool_func = tool_entry
        else:
            return {"error": f"Invalid tool registry entry for '{tool_name}'"}

        if not callable(tool_func):
            return {"error": f"Tool '{tool_name}' is not callable"}

        # Log the dynamic invocation
        register_event(
            backends,
            execution_id,
            EventTypes.TOOL_CALL,
            {
                "meta_tool": "call_tool",
                "invoked_tool": tool_name,
                "arguments": args,
            },
        )

        # Invoke the tool
        try:
            result = tool_func(**args)
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result,
            }
        except TypeError as e:
            # Argument mismatch
            return {
                "error": f"Argument error for '{tool_name}': {e}",
                "tool_name": tool_name,
            }
        except Exception as e:
            return {
                "error": f"Tool '{tool_name}' failed: {e}",
                "tool_name": tool_name,
            }

    return call_tool
