"""LLM node operational validation.

Calls shared operational validation + LLM-specific backend validation.
"""

from typing import Dict, Any
from ....types import Backends
from ....validation.operational import validate_operational, OperationalValidationError


def validate_llm_node_runtime(
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """Validate runtime state for LLM node."""
    context = validate_operational(execution_id, backends)

    try:
        backends.workflow.get_current_workflow_name(execution_id)
    except Exception as e:
        raise OperationalValidationError(f"Cannot access workflow backend: {e}")

    return context
