"""
Operational validation - validates runtime state before node execution.

This validates that the context and backends are in a valid state
for node execution. Runs before each node executes so that operational
code can trust the structure and avoid defensive programming.

Fail-fast: If validation fails, raise immediately with clear message.
"""

from typing import Dict, Any

from ..types import Backends, SoeError


class OperationalValidationError(SoeError):
    """Raised when operational context is invalid."""
    pass


def validate_operational(
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """
    Validate that operational context exists and has required structure.

    Call this before any node execution to ensure __operational__ is valid.
    Returns the context so caller doesn't need to fetch it again.

    Args:
        execution_id: The execution ID
        backends: Backend services

    Returns:
        The validated context dict

    Raises:
        OperationalValidationError: If context or __operational__ is invalid
    """
    context = backends.context.get_context(execution_id)

    if not context:
        raise OperationalValidationError(
            f"No context found for execution_id '{execution_id}'. "
            f"Context must be initialized before node execution."
        )

    operational = context.get("__operational__")

    if operational is None:
        raise OperationalValidationError(
            f"Missing '__operational__' in context for execution_id '{execution_id}'. "
            f"Call initialize_operational_context() before node execution."
        )

    required_fields = ["signals", "nodes", "llm_calls", "tool_calls", "errors", "main_execution_id"]
    missing = [f for f in required_fields if f not in operational]

    if missing:
        raise OperationalValidationError(
            f"Invalid '__operational__' structure for execution_id '{execution_id}'. "
            f"Missing fields: {missing}"
        )

    if not isinstance(operational["signals"], list):
        raise OperationalValidationError(
            f"Invalid '__operational__.signals' - must be a list, got {type(operational['signals']).__name__}"
        )

    if not isinstance(operational["nodes"], dict):
        raise OperationalValidationError(
            f"Invalid '__operational__.nodes' - must be a dict, got {type(operational['nodes']).__name__}"
        )

    if not isinstance(operational["llm_calls"], int):
        raise OperationalValidationError(
            f"Invalid '__operational__.llm_calls' - must be an int, got {type(operational['llm_calls']).__name__}"
        )

    if not isinstance(operational["tool_calls"], int):
        raise OperationalValidationError(
            f"Invalid '__operational__.tool_calls' - must be an int, got {type(operational['tool_calls']).__name__}"
        )

    if not isinstance(operational["errors"], int):
        raise OperationalValidationError(
            f"Invalid '__operational__.errors' - must be an int, got {type(operational['errors']).__name__}"
        )

    return context


def validate_backends(backends: Backends) -> None:
    """
    Validate that backends has required attributes.

    Args:
        backends: Backend services

    Raises:
        OperationalValidationError: If backends is invalid
    """
    required = ["context", "workflow"]

    for attr in required:
        if not hasattr(backends, attr) or getattr(backends, attr) is None:
            raise OperationalValidationError(
                f"Invalid backends: missing required attribute '{attr}'"
            )
