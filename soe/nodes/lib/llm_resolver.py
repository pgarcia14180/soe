"""
Shared LLM Resolver and Parser.

Handles the orchestration of LLM calls, including:
1. Parsing text responses into Pydantic models
2. Removing thinking tags
3. Extracting JSON from markdown
4. Retrying on validation errors

Used by LLM and Agent nodes.
"""

import json
import re
from typing import Type, Dict, Any, TypeVar
from pydantic import BaseModel, ValidationError
from ...types import CallLlm

T = TypeVar("T", bound=BaseModel)


def resolve_llm_call(
    call_llm: CallLlm,
    input_data: BaseModel,
    config: Dict[str, Any],
    response_model: Type[T],
    max_retries: int = 3,
) -> T:
    """
    Execute the LLM call loop:
    1. Convert input_data to JSON string
    2. Augment with format instructions for response_model
    3. Call LLM
    4. Parse and Validate
    5. Retry on failure
    """
    try:
        prompt_base = input_data.model_dump_json()
    except Exception as e:
        raise ValueError(f"Failed to serialize input model: {e}")

    instructions = _get_format_instructions(response_model)
    current_prompt = f"{prompt_base}\n\n{instructions}"

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response_text = call_llm(current_prompt, config)
        except Exception as e:
            raise e

        try:
            return _parse_response(response_text, response_model)
        except (ValidationError, ValueError) as e:
            last_error = e
            if attempt == max_retries:
                break

            error_msg = _format_validation_error(e)
            current_prompt += f"\n\nPrevious response: {response_text}{error_msg}"

    raise Exception(f"Max retries ({max_retries}) exceeded. Last error: {last_error}")


def _get_format_instructions(model: Type[BaseModel]) -> str:
    """Generate instructions for JSON output based on the model schema."""
    schema = model.model_json_schema()
    return (
        f"Respond ONLY with a valid JSON object matching this schema:\n"
        f"{json.dumps(schema)}\n"
        f"Do not return the schema itself. Return a JSON instance of the schema."
    )


def _format_validation_error(error: Exception) -> str:
    """Format validation errors with specific field information."""
    if isinstance(error, ValidationError):
        field_errors = [
            f"  - {'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in error.errors()
        ]
        return (
            "\n\nValidation failed. Fix these fields:\n"
            + "\n".join(field_errors)
            + "\n\nRespond with valid JSON."
        )
    return f"\n\nJSON parse error: {error}. Output valid JSON."


def _parse_response(text: str, model: Type[T]) -> T:
    """
    Parse text response into a Pydantic model.
    Removes <think> tags and extracts JSON from markdown blocks if present.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    json_str = _extract_json(text)
    return model.model_validate_json(json_str)


def _extract_json(text: str) -> str:
    """Extract JSON from text, handling nested objects and arrays."""
    text = text.strip()

    match = re.search(r"```(?:json)?\s*([\[\{].*?[\]\}])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    for i, char in enumerate(text):
        if char in "{[":
            return _extract_balanced(text, i)
    return text


def _extract_balanced(text: str, start: int) -> str:
    """Extract balanced JSON from start position."""
    open_char = text[start]
    close_char = "}" if open_char == "{" else "]"
    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == open_char:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]
