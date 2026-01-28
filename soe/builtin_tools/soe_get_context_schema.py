"""Built-in context schema retrieval tool."""

from typing import Dict, Any, Callable, Optional


def create_soe_get_context_schema_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_get_context_schema tool.

    Args:
        execution_id: ID to access context schema data via backends
        backends: Backend services to fetch context schema
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_get_context_schema function
    """

    def soe_get_context_schema(
        field_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get context schema information from the current execution.

        Args:
            field_name: If provided, get only this specific field's definition.
                       If None, returns the full schema.

        Returns:
            If field_name provided: {"field_name": "...", "definition": {...}}
            Otherwise: Full schema dict of field_name -> field_definition
        """
        schema = backends.context_schema.get_context_schema(execution_id)

        if schema is None:
            schema = {}

        if field_name:
            if field_name in schema:
                return {
                    "field_name": field_name,
                    "definition": schema[field_name],
                }
            else:
                return {
                    "error": f"Field '{field_name}' not found in context schema",
                    "available": list(schema.keys()),
                }

        return schema

    return soe_get_context_schema
