"""Agent node operational validation.

Calls shared operational validation + Agent-specific backend validation.
"""

from typing import Dict, Any
from ....types import Backends
from ....validation.operational import validate_operational, OperationalValidationError


def validate_agent_node_runtime(
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """Validate runtime state for Agent node."""
    context = validate_operational(execution_id, backends)

    try:
        backends.workflow.get_current_workflow_name(execution_id)
        backends.workflow.get_workflows_registry(execution_id)
    except Exception as e:
        raise OperationalValidationError(f"Cannot access workflow backend: {e}")

    return context
