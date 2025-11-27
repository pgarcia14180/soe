"""
Router node validation.

- config.py: Config validation at orchestration start
- operational.py: Runtime validation before execution (fail-fast)
"""

from .config import validate_node_config
from .operational import validate_router_node_runtime

__all__ = ["validate_node_config", "validate_router_node_runtime"]
