"""
Agent loop state management

This module defines the internal state that persists across the agent's
execution loop. When an `identity` is configured, the conversation history
is persisted to the backend, allowing it to be shared across different
node executions.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

if TYPE_CHECKING:
    from ....types import Backends


class AgentLoopState(BaseModel):
    """
    Internal state for the agent execution loop.

    When `identity` is None, this state is local to a single agent node
    execution. When `identity` is set, conversation history is loaded from
    and saved to the conversation_history backend, enabling persistence
    across different node executions.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool_responses: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 10
    history_key: Optional[str] = None
    _backends: Optional["Backends"] = PrivateAttr(default=None)

    @classmethod
    def create(
        cls,
        history_key: Optional[str] = None,
        backends: Optional["Backends"] = None,
        max_retries: int = 10,
    ) -> "AgentLoopState":
        """
        Factory method to create AgentLoopState, optionally loading
        existing conversation history from backend.

        Args:
            history_key: Optional key for persistent conversation history (main_execution_id)
            backends: Backends container (required if history_key is set)
            max_retries: Maximum retry count

        Returns:
            AgentLoopState instance, with history loaded if history_key exists
        """
        state = cls(max_retries=max_retries, history_key=history_key)
        state._backends = backends

        if history_key and backends and backends.conversation_history:
            state.conversation_history = backends.conversation_history.get_conversation_history(history_key)

        return state

    def add_tool_response(self, tool_name: str, result: Any) -> None:
        """Record a successful tool response."""
        self.tool_responses[tool_name] = result
        entry = {
            "role": "tool",
            "tool_name": tool_name,
            "content": str(result),
        }
        self.conversation_history.append(entry)
        self._persist_entry(entry)

    def add_tool_error(self, tool_name: str, error: str) -> None:
        """Record a tool execution error."""
        error_msg = f"Error executing {tool_name}: {error}"
        self.tool_responses[tool_name] = error_msg
        self.errors.append(error_msg)
        entry = {
            "role": "tool_error",
            "tool_name": tool_name,
            "content": error_msg,
        }
        self.conversation_history.append(entry)
        self._persist_entry(entry)
        self.retry_count += 1

    def add_system_error(self, error: str) -> None:
        """Record a system-level error (e.g., invalid tool name)."""
        self.errors.append(error)
        entry = {
            "role": "system_error",
            "content": error,
        }
        self.conversation_history.append(entry)
        self._persist_entry(entry)
        self.retry_count += 1

    def _persist_entry(self, entry: Dict[str, str]) -> None:
        """Persist a single entry to the backend if history_key is set."""
        if self.history_key and self._backends and self._backends.conversation_history:
            self._backends.conversation_history.append_to_conversation_history(
                self.history_key, entry
            )

    def can_retry(self) -> bool:
        """Check if we can still retry."""
        return self.retry_count < self.max_retries

    def get_execution_state(self) -> str:
        """
        Determine current execution state for prompt selection.

        Returns one of:
        - 'initial': No tool calls yet
        - 'tool_response': Has successful tool responses
        - 'tool_error': Has tool errors
        - 'retry': Has system errors (e.g., invalid tool name)
        """
        if not self.conversation_history:
            return "initial"

        last_entry = self.conversation_history[-1]
        role = last_entry.get("role", "")

        if role == "tool_error":
            return "tool_error"
        elif role == "system_error":
            return "retry"
        elif role == "tool":
            return "tool_response"

        return "initial"

    def get_context_for_llm(self) -> str:
        """
        Format the conversation history for inclusion in LLM prompts.
        """
        if not self.conversation_history:
            return ""

        parts = []
        for entry in self.conversation_history:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            tool_name = entry.get("tool_name", "")

            if role == "tool":
                parts.append(f"[Tool: {tool_name}]\n{content}")
            elif role == "tool_error":
                parts.append(f"[Tool Error: {tool_name}]\n{content}")
            elif role == "system_error":
                parts.append(f"[System Error]\n{content}")
            else:
                parts.append(content)

        return "\n\n".join(parts)
