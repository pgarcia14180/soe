"""
Schema validation utilities for Pydantic model generation.

Converts schema definitions to Pydantic models for runtime validation.
Logic extracted from backends to centralize in lib.
"""

from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, create_model, Field
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

        # Get Python type
        type_name = field_def.get("type", "any").lower()
        python_type = TYPE_MAPPING.get(type_name, Any)

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

    return create_model(model_name, **fields)


def validate_against_schema(
    data: Any,
    schema: Dict[str, Any],
    model_name: str = "ValidationModel"
) -> BaseModel:
    """
    Validate data against a schema.

    Args:
        data: The data to validate (dict or JSON string)
        schema: The schema definition
        model_name: Name for the validation model

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationError: If data doesn't match schema
    """
    # Parse JSON string if needed
    if isinstance(data, str):
        data = json.loads(data)

    # Create model and validate
    model_class = schema_to_pydantic(schema, model_name)
    return model_class(**data)


def get_pydantic_model_for_fields(
    schema: Dict[str, Any],
    field_names: list[str],
    model_name: str = "DynamicModel"
) -> Optional[Type[BaseModel]]:
    """
    Create a Pydantic model for specific fields from a schema.

    Args:
        schema: Full schema dict
        field_names: List of field names to include
        model_name: Name for the generated model

    Returns:
        Pydantic model class or None if no matching fields
    """
    if not schema:
        return None

    # Filter to specific fields
    filtered_schema = {k: v for k, v in schema.items() if k in field_names}

    if not filtered_schema:
        return None

    return schema_to_pydantic(filtered_schema, model_name)
