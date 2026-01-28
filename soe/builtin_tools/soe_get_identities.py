"""Built-in identity retrieval tool."""

from typing import Dict, Any, Callable, Optional


def create_soe_get_identities_tool(
    execution_id: str,
    backends,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory function to create soe_get_identities tool.

    Args:
        execution_id: ID to access identity data via backends
        backends: Backend services to fetch identities
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_get_identities function
    """

    def soe_get_identities(
        identity_name: Optional[str] = None,
        list_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Get identity information from the current execution.

        Args:
            identity_name: If provided, get only this specific identity's system prompt.
                          If None, returns info about all identities.
            list_only: If True, only return identity names (not full system prompts).
                      Default is False.

        Returns:
            If list_only=True: {"identity_names": ["assistant", "expert", ...]}
            If identity_name provided: {"identity_name": "...", "system_prompt": "..."}
            Otherwise: Full dict of identity_name -> system_prompt
        """
        identities = backends.identity.get_identities(execution_id)

        if identities is None:
            identities = {}

        if list_only:
            return {"identity_names": list(identities.keys())}

        if identity_name:
            if identity_name in identities:
                return {
                    "identity_name": identity_name,
                    "system_prompt": identities[identity_name],
                }
            else:
                return {
                    "error": f"Identity '{identity_name}' not found",
                    "available": list(identities.keys()),
                }

        return identities

    return soe_get_identities
