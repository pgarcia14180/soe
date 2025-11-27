"""
Built-in tool: copy_context
Allows agents to copy context fields between executions or within the same execution.
"""

from typing import Dict, Any, Optional


def create_soe_copy_context_tool(backends, execution_id: str, tools_registry=None):
    """
    Factory that creates a copy_context tool bound to the current execution.

    Args:
        backends: Backend instances (needs context backend)
        execution_id: Current execution ID
        tools_registry: Tool registry (unused, for interface compatibility)

    Returns:
        Configured tool function
    """

    def copy_context(
        source_execution_id: Optional[str] = None,
        fields: Optional[Dict[str, str]] = None,
        all_fields: bool = False,
        target_execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Copy context fields between executions or within the same execution.

        Args:
            source_execution_id: Execution ID to copy from (default: current)
            fields: Dict of {source_field: target_field} to copy
            all_fields: If True, copy all non-operational fields
            target_execution_id: Execution ID to copy to (default: current)

        Returns:
            Dict with copy results
        """
        source_id = source_execution_id or execution_id
        target_id = target_execution_id or execution_id

        # Get source context
        source_context = backends.context.get_context(source_id)

        # Filter out operational fields
        source_filtered = {k: v for k, v in source_context.items() if not k.startswith("__")}

        # Get target context
        target_context = backends.context.get_context(target_id)

        copied_fields = {}

        if all_fields:
            # Copy all non-operational fields
            for field, value in source_filtered.items():
                target_context[field] = value
                copied_fields[field] = field
        elif fields:
            # Copy specific field mappings
            for source_field, target_field in fields.items():
                if source_field in source_filtered:
                    target_context[target_field] = source_filtered[source_field]
                    copied_fields[source_field] = target_field
                else:
                    return {"error": f"Source field '{source_field}' not found in execution {source_id}"}
        else:
            return {"error": "Must specify either 'fields' mapping or 'all_fields=True'"}

        # Save target context
        backends.context.save_context(target_id, target_context)

        return {
            "status": "copied",
            "source_execution": source_id,
            "target_execution": target_id,
            "fields_copied": copied_fields,
        }

    return copy_context
