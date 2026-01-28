"""Built-in identity injection tool."""

from typing import Dict, Any, Callable
from ..types import EventTypes
from ..lib.register_event import register_event


def create_soe_inject_identity_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_inject_identity tool.

    Args:
        execution_id: ID to access identity data via backends
        backends: Backend services to fetch/update identities
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_inject_identity function that can add/update identities
    """

    def soe_inject_identity(identity_name: str, system_prompt: str) -> Dict[str, Any]:
        """
        Add or update an identity definition.

        Args:
            identity_name: Name/key for the identity
            system_prompt: The system prompt text for this identity

        Returns:
            Success confirmation with identity info and action taken
        """
        identities = backends.identity.get_identities(execution_id)

        if identities is None:
            identities = {}

        action = "updated" if identity_name in identities else "created"

        identities[identity_name] = system_prompt
        backends.identity.save_identities(execution_id, identities)

        register_event(
            backends,
            execution_id,
            EventTypes.NODE_EXECUTION,
            {
                "tool": "soe_inject_identity",
                "identity_name": identity_name,
                "action": action,
            },
        )

        return {
            "success": True,
            "identity_name": identity_name,
            "action": action,
            "message": f"Successfully {action} identity '{identity_name}'",
        }

    return soe_inject_identity
