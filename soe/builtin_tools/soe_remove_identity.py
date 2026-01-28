"""Built-in identity removal tool."""

from typing import Dict, Any, Callable
from ..types import EventTypes
from ..lib.register_event import register_event


def create_soe_remove_identity_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_remove_identity tool.

    Args:
        execution_id: ID to access identity data via backends
        backends: Backend services to fetch/update identities
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_remove_identity function that can remove identities
    """

    def soe_remove_identity(identity_name: str) -> Dict[str, Any]:
        """
        Remove an identity definition.

        Args:
            identity_name: Name of the identity to remove

        Returns:
            Success confirmation with removed identity info
        """
        identities = backends.identity.get_identities(execution_id)

        if identities is None or identity_name not in identities:
            raise ValueError(
                f"Identity '{identity_name}' not found"
            )

        del identities[identity_name]
        backends.identity.save_identities(execution_id, identities)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_remove_identity",
                "identity_name": identity_name,
            },
        )

        return {
            "removed": True,
            "identity_name": identity_name,
            "message": f"Successfully removed identity '{identity_name}'",
        }

    return soe_remove_identity
