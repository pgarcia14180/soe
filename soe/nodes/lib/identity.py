"""
Shared identity utilities for LLM and Agent nodes.

This module handles identity retrieval and system prompt generation
for nodes that support identity-based persona/role configuration.

Identities are stored per execution (main_execution_id) and define the initial
system prompt that will be used when conversation history starts.

Identity format is simple: identity_name -> system_prompt (string)
Example:
    assistant: "You are a helpful assistant."
    coding_expert: "You are an expert programmer."
"""

from typing import Dict, Any, Optional
from ...types import Backends


def get_system_prompt_from_identity(
    identity: Optional[str],
    main_execution_id: str,
    backends: Backends,
) -> Optional[str]:
    """
    Get the system prompt for an identity.

    Looks up the identity's system prompt from the identity backend using the
    main_execution_id and identity key.

    Args:
        identity: The identity key (e.g., "assistant", "coding_assistant")
        main_execution_id: Main execution ID for identity lookup
        backends: Backend services

    Returns:
        System prompt string or None if not found
    """
    if not identity or not backends.identity:
        return None

    if hasattr(backends.identity, 'get_identity'):
        return backends.identity.get_identity(main_execution_id, identity)

    identities = backends.identity.get_identities(main_execution_id)
    if not identities:
        return None

    return identities.get(identity)


def format_system_prompt_for_history(system_prompt: Optional[str]) -> str:
    """
    Format the system prompt for inclusion in conversation history.

    Args:
        system_prompt: The system prompt string

    Returns:
        Formatted system prompt or empty string
    """
    if not system_prompt:
        return ""
    return f"[system]: {system_prompt}"
