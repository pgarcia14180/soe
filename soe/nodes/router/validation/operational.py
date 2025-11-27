"""Router node operational validation.

Calls shared operational validation. Router has no additional backend requirements.
"""

from typing import Dict, Any
from ....types import Backends
from ....validation.operational import validate_operational, OperationalValidationError


def validate_router_node_runtime(
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """Validate runtime state for Router node. Delegates to shared validation."""
    return validate_operational(execution_id, backends)
