"""
Built-in tool: get_context
Allows agents to read context fields dynamically.
"""

from typing import Optional, List, Any, Dict


def create_soe_get_context_tool(backends, execution_id: str, tools_registry=None):
    """
    Factory that creates a get_context tool bound to the current execution.

    Args:
        backends: Backend instances (needs context backend)
        execution_id: Current execution ID
        tools_registry: Tool registry (unused, for interface compatibility)

    Returns:
        Configured tool function
    """

    def get_context(
        field: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Read context fields from the current execution.

        Args:
            field: Single field name to read (returns just that value)
            fields: List of field names to read (returns dict of values)

        If neither field nor fields is provided, returns all context.

        Returns:
            Context data (single value, dict of values, or full context)
        """
        context = backends.context.get_context(execution_id)

        # Filter out operational data
        filtered = {k: v for k, v in context.items() if not k.startswith("__")}

        if field:
            return {field: filtered.get(field)}
        elif fields:
            return {f: filtered.get(f) for f in fields}
        else:
            return filtered

    return get_context
