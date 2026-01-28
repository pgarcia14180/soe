"""Built-in context schema field removal tool."""

from typing import Dict, Any, Callable
from ..types import EventTypes
from ..lib.register_event import register_event


def create_soe_remove_context_schema_field_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_remove_context_schema_field tool.

    Args:
        execution_id: ID to access context schema data via backends
        backends: Backend services to fetch/update context schema
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_remove_context_schema_field function
    """

    def soe_remove_context_schema_field(field_name: str) -> Dict[str, Any]:
        """
        Remove a field from the context schema.

        Args:
            field_name: Name of the field to remove

        Returns:
            Success confirmation with removed field info
        """
        schema = backends.context_schema.get_context_schema(execution_id)

        if schema is None or field_name not in schema:
            raise ValueError(
                f"Field '{field_name}' not found in context schema"
            )

        del schema[field_name]
        backends.context_schema.save_context_schema(execution_id, schema)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_remove_context_schema_field",
                "field_name": field_name,
            },
        )

        return {
            "removed": True,
            "field_name": field_name,
            "message": f"Successfully removed field '{field_name}' from context schema",
        }

    return soe_remove_context_schema_field
