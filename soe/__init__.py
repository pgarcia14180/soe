"""
Orchestration Engine - MVP
Agent orchestration with event-driven workflow engine
"""

from .broker import orchestrate, broadcast_signals
from .nodes import (
    AgentRequest,
    AgentResponse,
    ToolNodeConfigurationError,
    ToolParameterError,
)
from .types import (
    # Backend protocols - for building custom backends
    Backends,
    ContextBackend,
    WorkflowBackend,
    TelemetryBackend,
    ConversationHistoryBackend,
    ContextSchemaBackend,
    IdentityBackend,
    # LLM protocol - for integrating custom LLM providers
    CallLlm,
)
from .init import create_all_nodes, setup_orchestration

__all__ = [
    # Core functions
    "orchestrate",
    "broadcast_signals",
    # Easy setup
    "create_all_nodes",
    "setup_orchestration",
    # Agent types
    "AgentRequest",
    "AgentResponse",
    # Tool errors
    "ToolNodeConfigurationError",
    "ToolParameterError",
    # Backend protocols
    "Backends",
    "ContextBackend",
    "WorkflowBackend",
    "TelemetryBackend",
    "ConversationHistoryBackend",
    "ContextSchemaBackend",
    "IdentityBackend",
    # LLM protocol
    "CallLlm",
]
