"""
Jinja template validation utilities.

Used during config validation to catch Jinja errors early.
"""

from jinja2 import Environment, BaseLoader, TemplateSyntaxError
from ..types import WorkflowValidationError


def _dummy_accumulated_filter(value):
    """Dummy accumulated filter for validation - just returns value as list."""
    return [value] if value is not None else []


def validate_jinja_syntax(template: str, context_description: str) -> None:
    """
    Validate Jinja template syntax at config time.

    Called during config validation to catch Jinja errors early.

    Catches:
    - Unclosed braces {{ without }}
    - Unknown filters like | capitalize_all
    - Basic syntax errors

    Does NOT catch:
    - Runtime errors like division by zero (depends on context values)
    - Undefined variables (depends on context at runtime)

    Args:
        template: The Jinja template string to validate
        context_description: Description for error messages (e.g., "condition for signal 'DONE'")

    Raises:
        WorkflowValidationError: If template has syntax or filter errors
    """
    if not template or ("{{" not in template and "{%" not in template):
        return
    try:
        env = Environment(loader=BaseLoader())
        env.filters["accumulated"] = _dummy_accumulated_filter
        env.parse(template)
        env.from_string(template)
    except TemplateSyntaxError as e:
        raise WorkflowValidationError(
            f"{context_description}: Jinja syntax error - {e.message}"
        )
    except Exception as e:
        error_msg = str(e)
        if "filter" in error_msg.lower():
            raise WorkflowValidationError(
                f"{context_description}: {error_msg}"
            )
