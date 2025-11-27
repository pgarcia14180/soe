"""
Backend creation helpers for tests.
"""

import os
from typing import Set
from soe.local_backends import create_in_memory_backends


def _get_verbose_flags() -> Set[str]:
    """Get enabled verbose flags from SOE_VERBOSE environment variable"""
    verbose = os.environ.get("SOE_VERBOSE", "")
    if not verbose:
        return set()
    return set(flag.strip() for flag in verbose.split(","))


class VerboseContextWrapper:
    """Wrapper that logs context operations"""

    def __init__(self, backend):
        self._backend = backend

    def get_context(self, execution_id: str):
        ctx = self._backend.get_context(execution_id)
        print(f"\n[CONTEXT GET] {execution_id}: {ctx}")
        return ctx

    def save_context(self, execution_id: str, context):
        print(f"\n[CONTEXT SAVE] {execution_id}: {context}")
        return self._backend.save_context(execution_id, context)

    def cleanup_all(self):
        return self._backend.cleanup_all()


class VerboseTelemetryWrapper:
    """Wrapper that logs telemetry operations"""

    def __init__(self, backend):
        self._backend = backend

    def log_event(self, execution_id: str, event_type: str, **event_data):
        print(f"\n[TELEMETRY] {event_type}: {event_data}")
        return self._backend.log_event(execution_id, event_type, **event_data)

    def get_events(self, execution_id: str):
        return self._backend.get_events(execution_id)

    def cleanup_all(self):
        return self._backend.cleanup_all()


class VerboseConversationHistoryWrapper:
    """Wrapper that logs conversation history operations"""

    def __init__(self, backend):
        self._backend = backend

    def get_conversation_history(self, identity: str):
        history = self._backend.get_conversation_history(identity)
        print(f"\n[CONVERSATION GET] {identity}: {history}")
        return history

    def append_to_conversation_history(self, identity: str, entry):
        print(f"\n[CONVERSATION APPEND] {identity}: {entry}")
        return self._backend.append_to_conversation_history(identity, entry)

    def save_conversation_history(self, identity: str, history):
        print(f"\n[CONVERSATION SAVE] {identity}: {history}")
        return self._backend.save_conversation_history(identity, history)

    def delete_conversation_history(self, identity: str):
        return self._backend.delete_conversation_history(identity)

    def cleanup_all(self):
        return self._backend.cleanup_all()


def create_test_backends(test_name: str = "test"):
    """
    Create in-memory backends for testing.

    Uses in-memory backends for fast, isolated tests without file I/O.

    Verbose logging controlled via SOE_VERBOSE environment variable:
      SOE_VERBOSE=context,telemetry,conversation_history

    Args:
        test_name: Identifier for test (unused with in-memory backends, kept for API compatibility)

    Returns:
        LocalBackends instance with in-memory backends
    """
    backends = create_in_memory_backends()

    verbose_flags = _get_verbose_flags()

    if "context" in verbose_flags:
        backends.context = VerboseContextWrapper(backends.context)

    if "telemetry" in verbose_flags and backends.telemetry:
        backends.telemetry = VerboseTelemetryWrapper(backends.telemetry)

    if "conversation_history" in verbose_flags and backends.conversation_history:
        backends.conversation_history = VerboseConversationHistoryWrapper(backends.conversation_history)

    return backends
