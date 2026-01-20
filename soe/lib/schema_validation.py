"""
Schema validation utilities for Pydantic model generation.

Converts schema definitions to Pydantic models for runtime validation.
Logic extracted from backends to centralize in lib.
"""

from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, create_model, Field, RootModel
import json


# Type mapping from schema types to Python types
TYPE_MAPPING = {
    "string": str,
    "text": str,
    "str": str,
    "integer": int,
    "int": int,
    "number": float,
    "float": float,
    "boolean": bool,
    "bool": bool,
    "list": list,
    "array": list,
    "dict": dict,
    "object": dict,
    "any": Any,
}


def _schema_field_to_type(field_def: Any, model_name: str) -> Any:
    """Resolve a schema field definition to a Python type (supports nested properties/items)."""
    if isinstance(field_def, str):
        field_def = {"type": field_def}

    if not isinstance(field_def, dict):
        return Any

    type_name = field_def.get("type", "any").lower()

    if type_name in ("object", "dict"):
        properties = field_def.get("properties")
        if isinstance(properties, dict) and properties:
            nested_model = schema_to_pydantic(properties, model_name=f"{model_name}Nested")
            return nested_model
        return dict

    if type_name in ("list", "array"):
        items = field_def.get("items")
        if items:
            if isinstance(items, str):
                items = {"type": items}
            item_type = _schema_field_to_type(items, model_name=f"{model_name}Item")
            return List[item_type]
        return list

    return TYPE_MAPPING.get(type_name, Any)


def schema_to_root_model(
    field_def: Dict[str, Any],
    model_name: str = "RootModel"
) -> Type[BaseModel]:
    """Convert a single field schema into a RootModel for flat output validation."""
    if isinstance(field_def, str):
        field_def = {"type": field_def}

    root_type = _schema_field_to_type(field_def, model_name=model_name)

    class DynamicRoot(RootModel[root_type]):
        pass

    DynamicRoot.__name__ = model_name
    return DynamicRoot


def schema_to_pydantic(
    schema: Dict[str, Any],
    model_name: str = "DynamicModel"
) -> Type[BaseModel]:
    """
    Convert a schema dict to a Pydantic model.

    Schema format:
    {
        "field_name": {
            "type": "string",
            "description": "Field description",  # optional
            "required": true,  # optional, default true
            "default": null  # optional
        }
    }

    Args:
        schema: Dict mapping field names to field definitions
        model_name: Name for the generated Pydantic model

    Returns:
        Dynamically created Pydantic model class
    """
    fields = {}

    for field_name, field_def in schema.items():
        # Handle simple type definition (just the type name as string)
        if isinstance(field_def, str):
            field_def = {"type": field_def}

        # Get Python type (supports nested properties/items)
        python_type = _schema_field_to_type(field_def, model_name=f"{model_name}{field_name.title()}")

        # Get field metadata
        description = field_def.get("description", "")
        required = field_def.get("required", True)
        default = field_def.get("default", None)

        # Build field tuple
        if required and default is None:
            # Required field with no default
            if description:
                field_info = (python_type, Field(..., description=description))
            else:
                field_info = (python_type, ...)
        else:
            # Optional field or has default
            if description:
                field_info = (Optional[python_type], Field(default=default, description=description))
            else:
                field_info = (Optional[python_type], default)

        fields[field_name] = field_info

    # Allow extra fields to be preserved (important for nested partial schemas)
    return create_model(model_name, **fields, __config__={"extra": "allow"})
