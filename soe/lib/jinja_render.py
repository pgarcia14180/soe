"""
Jinja template rendering utilities for prompt processing.
"""

import re
from typing import Dict, Any, Set, List, Tuple

from jinja2 import Environment, BaseLoader, TemplateSyntaxError

from .context_fields import get_field


def _create_accumulated_filter(full_context: Dict[str, Any]):
    """Create an accumulated filter that returns full history for a field."""
    def accumulated_filter(value):
        """
        Return the full accumulated history list for a context field.

        Usage in templates:
            {{ context.field | accumulated }}  - returns full list
            {{ context.field | accumulated | length }}  - count of items
            {{ context.field | accumulated | join(', ') }}  - join all items

        If history has exactly one entry and it's a list, returns that list
        (common case: initial context passed a list as value).
        """
        # Find the field in full_context by matching the last value
        for key, hist_list in full_context.items():
            if key.startswith("__"):
                continue
            if isinstance(hist_list, list) and hist_list and hist_list[-1] == value:
                # If history has exactly one entry and it's a list, return that list
                if len(hist_list) == 1 and isinstance(hist_list[0], list):
                    return hist_list[0]
                return hist_list
        # Fallback: return value as single-item list
        return [value] if value is not None else []

    return accumulated_filter


def _extract_context_variables(template: str) -> Set[str]:
    """Extract variable names from a Jinja template."""
    if not template:
        return set()

    variables = set()

    dot_pattern = r'\{\{[^}]*context\.([a-zA-Z_][a-zA-Z0-9_]*)'
    for match in re.finditer(dot_pattern, template):
        variables.add(match.group(1))

    bracket_pattern = r"\{\{[^}]*context\[['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]"
    for match in re.finditer(bracket_pattern, template):
        variables.add(match.group(1))

    return variables


def get_context_for_prompt(
    full_context: Dict[str, Any],
    template: str
) -> Tuple[Dict[str, Any], List[str]]:
    """Extract the context needed for a prompt template."""
    required_fields = _extract_context_variables(template)
    filtered_context = {}
    warnings = []

    for field in required_fields:
        if field not in full_context:
            warnings.append(f"Context field '{field}' referenced in prompt but not found in context")
        else:
            value = get_field(full_context, field)
            if value is None:
                warnings.append(f"Context field '{field}' is None")
                filtered_context[field] = None
            elif value == "":
                warnings.append(f"Context field '{field}' is empty string")
                filtered_context[field] = ""
            else:
                filtered_context[field] = value

    return filtered_context, warnings


def render_prompt(prompt: str, context: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Render a Jinja template prompt with the given context."""
    if not prompt:
        return prompt, []

    if "{{" not in prompt and "{%" not in prompt:
        return prompt, []

    _, warnings = get_context_for_prompt(context, prompt)

    unwrapped = {k: get_field(context, k) for k in context if not k.startswith("__")}
    for k, v in context.items():
        if k.startswith("__"):
            unwrapped[k] = v

    try:
        jinja_env = Environment(loader=BaseLoader())
        # Register custom filters
        jinja_env.filters["accumulated"] = _create_accumulated_filter(context)
        template = jinja_env.from_string(prompt)
        rendered = template.render(context=unwrapped)
        return rendered, warnings
    except TemplateSyntaxError as e:
        warnings.append(f"Jinja syntax error: {e}")
        return prompt, warnings
    except Exception as e:
        warnings.append(f"Template rendering error: {e}")
        return prompt, warnings
