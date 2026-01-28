"""Built-in context schema field injection tool."""

import json
from typing import Dict, Any, Callable
from ..types import EventTypes
from ..lib.register_event import register_event
from ..lib.yaml_parser import parse_yaml


def create_soe_inject_context_schema_field_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_inject_context_schema_field tool.

    Args:
        execution_id: ID to access context schema data via backends
        backends: Backend services to fetch/update context schema
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_inject_context_schema_field function
    """

    def soe_inject_context_schema_field(
        field_name: str,
        field_definition: str,
    ) -> Dict[str, Any]:
        """
        Add or update a field in the context schema.

        Args:
            field_name: Name of the field to add/update
            field_definition: JSON or YAML string with field definition
                             (e.g., {"type": "string", "description": "..."})

        Returns:
            Success confirmation with field info and action taken
        """
        parsed_definition = None

        try:
            parsed_definition = json.loads(field_definition)
        except json.JSONDecodeError:
            parsed_definition = parse_yaml(field_definition)

        if not isinstance(parsed_definition, dict):
            raise ValueError("Field definition must be a dictionary/object")

        schema = backends.context_schema.get_context_schema(execution_id)

        if schema is None:
            schema = {}

        action = "updated" if field_name in schema else "created"

        schema[field_name] = parsed_definition
        backends.context_schema.save_context_schema(execution_id, schema)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_inject_context_schema_field",
                "field_name": field_name,
                "action": action,
            },
        )

        return {
            "success": True,
            "field_name": field_name,
            "action": action,
            "message": f"Successfully {action} field '{field_name}' in context schema",
        }

    return soe_inject_context_schema_field
