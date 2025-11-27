"""
Built-in tool: update_context
Allows agents to write context fields dynamically.
"""

from typing import Any, Dict


def create_soe_update_context_tool(backends, execution_id: str, tools_registry=None):
    """
    Factory that creates an update_context tool bound to the current execution.

    Args:
        backends: Backend instances (needs context backend)
        execution_id: Current execution ID
        tools_registry: Tool registry (unused, for interface compatibility)

    Returns:
        Configured tool function
    """

    def update_context(updates: Dict[str, Any]) -> Dict[str, str]:
        """
        Update context fields for the current execution.

        Args:
            updates: Dictionary of field names to values to set

        Returns:
            Confirmation of updated fields
        """
        if not updates:
            return {"status": "no updates provided"}

        # Don't allow updating operational fields
        filtered_updates = {
            k: v for k, v in updates.items()
            if not k.startswith("__")
        }

        if not filtered_updates:
            return {"status": "no valid updates (operational fields cannot be updated)"}

        # Get current context and update
        context = backends.context.get_context(execution_id)
        context.update(filtered_updates)
        backends.context.save_context(execution_id, context)

        return {
            "status": "updated",
            "fields": list(filtered_updates.keys())
        }

    return update_context
