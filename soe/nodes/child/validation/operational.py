"""Child node operational validation.

Calls shared operational validation + Child-specific backend validation.
"""

from typing import Dict, Any
from ....types import Backends
from ....validation.operational import validate_operational, OperationalValidationError


def validate_child_node_runtime(
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """Validate runtime state for Child node."""
    context = validate_operational(execution_id, backends)

    try:
        workflows_registry = backends.workflow.soe_get_workflows_registry(execution_id)
    except Exception as e:
        raise OperationalValidationError(f"Cannot access workflow backend: {e}")

    if not workflows_registry:
        raise OperationalValidationError(
            f"No workflows_registry found for execution_id '{execution_id}'"
        )

    return context
