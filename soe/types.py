"""
Types for orchestration system
"""

from __future__ import annotations

from typing import Protocol, Optional, Any, Dict, List


class TelemetryBackend(Protocol):
    """Protocol for telemetry backend"""

    def log_event(self, execution_id: str, event_type: str, **event_data) -> None:
        ...


class ContextBackend(Protocol):
    """Protocol for context backend"""

    def save_context(self, id: str, context: dict) -> None:
        ...

    def get_context(self, id: str) -> dict:
        ...


class WorkflowBackend(Protocol):
    """Protocol for workflow backend"""

    def save_workflows_registry(self, id: str, workflows: Dict[str, Any]) -> None:
        ...

    def soe_get_workflows_registry(self, id: str) -> Any:
        ...

    def save_current_workflow_name(self, id: str, name: str) -> None:
        ...

    def get_current_workflow_name(self, id: str) -> str:
        ...


class OrchestrateCaller(Protocol):
    """Protocol for orchestrate caller function"""

    def __call__(self, execution_id: str, signals: List[str]) -> None:
        ...


class BroadcastSignalsCaller(Protocol):
    """Protocol for broadcast signals caller function"""

    def __call__(self, execution_id: str, signals: List[str]) -> None:
        ...


class RouterNodeCaller(Protocol):
    """Protocol for router node caller function"""

    def __call__(self, execution_id: str, node_config: Dict[str, Any]) -> None:
        ...


class AgentNodeCaller(Protocol):
    """Protocol for agent node caller function"""

    def __call__(self, execution_id: str, node_config: Dict[str, Any]) -> None:
        ...


class ToolNodeCaller(Protocol):
    """Protocol for tool node caller function"""

    def __call__(self, execution_id: str, node_config: Dict[str, Any]) -> None:
        ...


class ChildNodeCaller(Protocol):
    """Protocol for child node caller function"""

    def __call__(self, execution_id: str, node_config: Dict[str, Any]) -> None:
        ...


class OrchestrateCaller(Protocol):
    """Protocol for starting child workflows (wrapper around orchestrate).

    Supports optional inheritance parameters:
    - inherit_config_from_id: Inherit workflows, identities, schema from existing execution
    - inherit_context_from_id: Inherit context from existing execution (resets operational)
    """

    def __call__(
        self,
        config: Any,
        initial_workflow_name: str,
        initial_signals: List[str],
        initial_context: Dict[str, Any],
        backends: "Backends",
        inherit_config_from_id: Optional[str] = None,
        inherit_context_from_id: Optional[str] = None,
    ) -> str:
        ...


class CallLlm(Protocol):
    """Protocol for LLM caller function"""

    def __call__(self, prompt: str, config: Dict[str, Any]) -> str:
        ...


class ConversationHistoryBackend(Protocol):
    """Protocol for conversation history backend"""

    def get_conversation_history(self, identity: str) -> List[Dict[str, Any]]:
        ...

    def append_to_conversation_history(self, identity: str, entry: Dict[str, Any]) -> None:
        ...

    def save_conversation_history(self, identity: str, history: List[Dict[str, Any]]) -> None:
        ...

    def delete_conversation_history(self, identity: str) -> None:
        ...


class ContextSchemaBackend(Protocol):
    """Protocol for context schema backend - stores workflow context field schemas.

    Context schemas define the structure and types of context fields used in workflows.
    These are keyed by execution_id (main_execution_id) so children can access parent's schemas.
    """

    def save_context_schema(self, execution_id: str, schema: Dict[str, Any]) -> None:
        """Save context schema for an execution."""
        ...

    def get_context_schema(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get context schema for an execution."""
        ...

    def delete_context_schema(self, execution_id: str) -> bool:
        """Delete context schema for an execution."""
        ...


class IdentityBackend(Protocol):
    """Protocol for identity backend - stores workflow identity definitions.

    Identities define the participating personas/roles in a workflow.
    These are used as the initial system prompt for conversation history.
    Keyed by execution_id (main_execution_id) so children can access parent's identities.

    Identity format is simple: identity_name -> system_prompt (string)
    Example:
        assistant: "You are a helpful assistant."
        coding_expert: "You are an expert programmer."
    """

    def save_identities(self, execution_id: str, identities: Dict[str, str]) -> None:
        """Save identity definitions for an execution."""
        ...

    def get_identities(self, execution_id: str) -> Optional[Dict[str, str]]:
        """Get all identity definitions for an execution."""
        ...

    def get_identity(self, execution_id: str, identity_name: str) -> Optional[str]:
        """Get a specific identity's system prompt."""
        ...

    def delete_identities(self, execution_id: str) -> bool:
        """Delete identity definitions for an execution."""
        ...


class Backends(Protocol):
    """Protocol for orchestration backends"""

    context: ContextBackend
    workflow: WorkflowBackend
    telemetry: Optional[TelemetryBackend]
    conversation_history: Optional[ConversationHistoryBackend]
    context_schema: Optional[ContextSchemaBackend]
    identity: Optional[IdentityBackend]


class SoeError(Exception):
    """Base class for all SOE exceptions"""
    pass


class WorkflowValidationError(SoeError):
    """Raised when workflow or node configuration is invalid (static/startup)"""
    pass
