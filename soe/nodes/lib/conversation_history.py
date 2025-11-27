"""
Shared conversation history utilities for LLM and Agent nodes.

This module handles conversation history retrieval, formatting, and saving
for nodes that support identity-based conversation persistence.
"""

from typing import Dict, Any, List, Optional, Tuple
from ...types import Backends


def get_conversation_history(
    execution_id: str,
    identity: Optional[str],
    backends: Backends,
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Get conversation history and history key for a node with identity.

    Identity enables conversation history. The key is main_execution_id,
    ensuring history persists across sub-orchestration boundaries.

    When the history is empty and an identity backend is configured,
    the identity's system prompt is injected as the first message.
    Both identity and context_schema are keyed by main_execution_id.

    Args:
        execution_id: Current execution ID
        identity: Identity key for conversation history
        backends: Backend services

    Returns:
        Tuple of (history_key, conversation_history list)
        history_key is None if no identity or no conversation backend
    """
    if not identity or not backends.conversation_history:
        return (None, [])

    context = backends.context.get_context(execution_id)
    main_id = context.get("__operational__", {}).get("main_execution_id", execution_id)
    history = backends.conversation_history.get_conversation_history(main_id)

    if not history and backends.identity:
        identities = backends.identity.get_identities(main_id)
        if identities and identity in identities:
            system_prompt = identities[identity]
            if system_prompt:
                history = [{"role": "system", "content": system_prompt}]
                backends.conversation_history.save_conversation_history(main_id, history)

    return (main_id, history)


def format_conversation_history(conversation_history: List[Dict[str, Any]]) -> str:
    """Format conversation history as a string for prompts."""
    if not conversation_history:
        return ""
    return "\n".join(
        f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')}"
        for msg in conversation_history
    )


def save_conversation_turn(
    history_key: Optional[str],
    conversation_history: List[Dict[str, Any]],
    user_content: str,
    assistant_content: str,
    backends: Backends,
) -> None:
    """Save a conversation turn (user + assistant) to history."""
    if not history_key or not backends.conversation_history:
        return

    conversation_history.append({"role": "user", "content": user_content})
    conversation_history.append({"role": "assistant", "content": str(assistant_content)})
    backends.conversation_history.save_conversation_history(history_key, conversation_history)
