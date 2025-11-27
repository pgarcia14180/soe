"""
Built-in tool: list_contexts
Allows agents to list available execution contexts.
"""

from typing import List, Dict, Any
import os
import json


def create_soe_list_contexts_tool(backends, execution_id: str, tools_registry=None):
    """
    Factory that creates a list_contexts tool bound to the current execution.

    Args:
        backends: Backend instances (needs context backend)
        execution_id: Current execution ID
        tools_registry: Tool registry (unused, for interface compatibility)

    Returns:
        Configured tool function
    """

    def list_contexts(include_current: bool = True) -> Dict[str, Any]:
        """
        List available execution contexts.

        Args:
            include_current: Whether to include current execution in list

        Returns:
            Dict with current_execution_id and list of context summaries
        """
        result = {
            "current_execution_id": execution_id,
            "contexts": []
        }

        # Get context storage directory from backend
        storage_dir = getattr(backends.context, 'storage_dir', None)
        if not storage_dir or not os.path.exists(storage_dir):
            return result

        for filename in os.listdir(storage_dir):
            if not filename.endswith('.json'):
                continue

            ctx_id = filename.replace('.json', '')

            if not include_current and ctx_id == execution_id:
                continue

            # Read minimal info from each context
            filepath = os.path.join(storage_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    ctx = json.load(f)

                # Get summary info
                ops = ctx.get("__operational__", {})
                result["contexts"].append({
                    "execution_id": ctx_id,
                    "is_current": ctx_id == execution_id,
                    "user_request": ctx.get("user_request", [])[-1] if ctx.get("user_request") else None,
                    "signals": ops.get("signals", [])[-5:],  # Last 5 signals
                    "node_count": sum(ops.get("nodes", {}).values()),
                })
            except Exception:
                continue

        return result

    return list_contexts
