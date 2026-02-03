"""
Dynamic Pydantic response model builder.
"""

from typing import Type, Any, Optional, List, Dict, Literal
from pydantic import RootModel
from pydantic import BaseModel, Field, create_model


def build_response_model(
    output_field: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    signal_options: Optional[List[Dict[str, str]]] = None,
) -> Type[BaseModel]:
    """Dynamically build a Pydantic response model based on requirements."""
    fields: Dict[str, Any] = {}

    root_schema = None
    if output_schema and isinstance(output_schema, type) and issubclass(output_schema, RootModel):
        # Use RootModel directly if no signal selection is needed (standard case for single output)
        if not signal_options or len(signal_options) <= 1:
            return output_schema
        root_schema = output_schema
    if output_field:
        if root_schema:
            root_type = root_schema.model_fields["root"].annotation
            fields[output_field] = (
                root_type,
                Field(..., description=f"The {output_field} value matching the expected schema")
            )
        else:
            fields[output_field] = (
                Any,
                Field(..., description=f"The {output_field} value")
            )
    else:
        fields["output"] = (
            str,
            Field(..., description="The final output/result")
        )

    if signal_options and len(signal_options) > 1:
        signal_names = [s["name"] for s in signal_options]
        signal_literal = Literal[tuple(signal_names)]

        descriptions = []
        for s in signal_options:
            if s.get("description"):
                descriptions.append(f"- {s['name']}: {s['description']}")
            else:
                descriptions.append(f"- {s['name']}")

        desc_text = "Select ALL signals that apply (can be none, one, or multiple):\n" + "\n".join(descriptions)

        fields["selected_signals"] = (
            List[signal_literal],
            Field(default=[], description=desc_text)
        )

    model_name = "DynamicResponse"
    if output_field:
        model_name = f"{output_field.title()}Response"

    return create_model(model_name, **fields)


def extract_output_from_response(
    response: BaseModel,
    output_field: Optional[str],
) -> Any:
    """Extract the output value from a dynamic response model."""
    if isinstance(response, RootModel):
        value = response.root
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value
    data = response.model_dump()
    if output_field and output_field in data:
        return data[output_field]
    return data.get("output")


def extract_signals_from_response(response: BaseModel) -> List[str]:
    """
    Extract the selected signals from a dynamic response model.
    Returns a list of signal names (can be empty).
    """
    data = response.model_dump()
    if isinstance(data, dict):
        signals = data.get("selected_signals", [])
        if isinstance(signals, list):
            return signals
    return []
