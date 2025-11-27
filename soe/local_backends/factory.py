"""
Factory for creating local backends
"""

from typing import Optional, Any
from .storage.context import LocalContextBackend
from .storage.workflow import LocalWorkflowBackend
from .storage.telemetry import LocalTelemetryBackend
from .storage.conversation_history import LocalConversationHistoryBackend
from .storage.schema import LocalContextSchemaBackend
from .storage.identity import LocalIdentityBackend
from .in_memory.context import InMemoryContextBackend
from .in_memory.workflow import InMemoryWorkflowBackend
from .in_memory.telemetry import InMemoryTelemetryBackend
from .in_memory.conversation_history import InMemoryConversationHistoryBackend
from .in_memory.schema import InMemoryContextSchemaBackend
from .in_memory.identity import InMemoryIdentityBackend


class LocalBackends:
    """Container for local backends"""

    def __init__(
        self,
        context_backend: Any,
        workflow_backend: Any,
        telemetry_backend: Optional[Any] = None,
        conversation_history_backend: Optional[Any] = None,
        context_schema_backend: Optional[Any] = None,
        identity_backend: Optional[Any] = None,
    ):
        self.context = context_backend
        self.workflow = workflow_backend
        self.telemetry = telemetry_backend
        self.conversation_history = conversation_history_backend
        self.context_schema = context_schema_backend
        self.identity = identity_backend

    def cleanup_all(self) -> None:
        """
        Cleanup all backend data

        This method is useful for test cleanup to remove all stored data
        """
        self.context.cleanup_all()
        self.workflow.cleanup_all()
        if self.telemetry:
            self.telemetry.cleanup_all()
        if self.conversation_history:
            self.conversation_history.cleanup_all()
        if self.context_schema:
            self.context_schema.cleanup_all()
        if self.identity:
            self.identity.cleanup_all()


def create_local_backends(
    context_storage_dir: str = "./orchestration_data/contexts",
    workflow_storage_dir: str = "./orchestration_data/workflows",
    telemetry_storage_dir: Optional[str] = None,
    conversation_history_storage_dir: Optional[str] = "./orchestration_data/conversations",
    context_schema_storage_dir: Optional[str] = "./orchestration_data/schemas",
    identity_storage_dir: Optional[str] = "./orchestration_data/identities",
) -> LocalBackends:
    """
    Create local file-based backends for testing and development

    Args:
        context_storage_dir: Directory for context storage
        workflow_storage_dir: Directory for workflow storage
        telemetry_storage_dir: Directory for telemetry storage (optional)
        conversation_history_storage_dir: Directory for conversation history storage (optional)
        context_schema_storage_dir: Directory for context schema storage (optional)
        identity_storage_dir: Directory for identity storage (optional)

    Returns:
        LocalBackends instance with context, workflow, and optional backends
    """
    context_backend = LocalContextBackend(context_storage_dir)
    workflow_backend = LocalWorkflowBackend(workflow_storage_dir)

    telemetry_backend = None
    if telemetry_storage_dir:
        telemetry_backend = LocalTelemetryBackend(telemetry_storage_dir)

    conversation_history_backend = None
    if conversation_history_storage_dir:
        conversation_history_backend = LocalConversationHistoryBackend(
            conversation_history_storage_dir
        )

    context_schema_backend = None
    if context_schema_storage_dir:
        context_schema_backend = LocalContextSchemaBackend(context_schema_storage_dir)

    identity_backend = None
    if identity_storage_dir:
        identity_backend = LocalIdentityBackend(identity_storage_dir)

    return LocalBackends(
        context_backend,
        workflow_backend,
        telemetry_backend,
        conversation_history_backend,
        context_schema_backend,
        identity_backend,
    )


def create_in_memory_backends() -> LocalBackends:
    """
    Create in-memory backends for testing

    Returns:
        LocalBackends instance with in-memory backends
    """
    return LocalBackends(
        context_backend=InMemoryContextBackend(),
        workflow_backend=InMemoryWorkflowBackend(),
        telemetry_backend=InMemoryTelemetryBackend(),
        conversation_history_backend=InMemoryConversationHistoryBackend(),
        context_schema_backend=InMemoryContextSchemaBackend(),
        identity_backend=InMemoryIdentityBackend(),
    )
