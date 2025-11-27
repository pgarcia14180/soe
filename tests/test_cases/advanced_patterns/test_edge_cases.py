"""
Edge case tests for valid but potentially unexpected behavior.

These are NOT errors - they document how SOE handles edge cases gracefully.
"""

import pytest
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_router_nodes, extract_signals


class TestJinjaEdgeCases:
    """Edge cases in Jinja condition evaluation."""

    def test_division_by_zero_silently_fails(self):
        """Division by zero in condition causes it to silently fail (not emit)."""
        backends = create_test_backends("edge_div_zero")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  DivisionNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: SHOULD_NOT_EMIT
        condition: "{{ 1 / 0 > 0 }}"
      - signal_name: FALLBACK
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        # Division by zero condition fails silently, FALLBACK still emits
        assert "SHOULD_NOT_EMIT" not in signals
        assert "FALLBACK" in signals
        backends.cleanup_all()

    def test_undefined_variable_silently_fails(self):
        """Undefined variable in condition causes it to silently fail."""
        backends = create_test_backends("edge_undefined")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  UndefinedNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: SHOULD_NOT_EMIT
        condition: "{{ context.nonexistent == 'value' }}"
      - signal_name: FALLBACK
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert "FALLBACK" in signals
        backends.cleanup_all()

    def test_single_braces_treated_as_literal(self):
        """Single braces { } are treated as literal strings, not Jinja."""
        backends = create_test_backends("edge_literal")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  LiteralNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: EMITS_ANYWAY
        condition: "{ not jinja }"
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        # Single braces are literal strings, which are truthy, so condition passes
        assert "EMITS_ANYWAY" in signals
        backends.cleanup_all()


class TestIgnoredFieldsEdgeCases:
    """Edge cases where wrong field names are silently ignored."""

    def test_when_instead_of_condition_always_emits(self):
        """Using 'when' instead of 'condition' means no condition = always emit."""
        backends = create_test_backends("edge_when")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  WhenNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ALWAYS_EMITS
        when: "{{ false }}"
"""
        # 'when' is ignored, so no condition means always emit
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert "ALWAYS_EMITS" in signals  # Emits because 'when' is ignored!
        backends.cleanup_all()

    def test_if_instead_of_condition_always_emits(self):
        """Using 'if' instead of 'condition' means no condition = always emit."""
        backends = create_test_backends("edge_if")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  IfNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ALWAYS_EMITS
        if: "{{ false }}"
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert "ALWAYS_EMITS" in signals  # Emits because 'if' is ignored!
        backends.cleanup_all()

    def test_extra_unknown_field_ignored(self):
        """Unknown fields in node config are silently ignored."""
        backends = create_test_backends("edge_extra")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  ExtraNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
    description: "This field doesn't exist but is ignored"
    priority: 100
    tags: [important, urgent]
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert "DONE" in signals  # Works fine, unknown fields ignored
        backends.cleanup_all()

    def test_empty_event_emissions_is_validation_error(self):
        """Empty event_emissions list is a validation error for router nodes."""
        from soe.nodes.router.validation import validate_node_config as validate_router
        from soe.types import WorkflowValidationError
        import pytest

        # Router nodes require at least one emission
        with pytest.raises(WorkflowValidationError, match="'event_emissions' is required"):
            validate_router({
                "event_triggers": ["START"],
                "event_emissions": []
            })


class TestSignalNameEdgeCases:
    """Edge cases with signal names."""

    def test_unicode_signal_names(self):
        """Unicode characters in signal names should work."""
        backends = create_test_backends("edge_unicode")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  UnicodeNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: "完成"
      - signal_name: "émojis_🎉_work"
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert "完成" in signals
        assert "émojis_🎉_work" in signals
        backends.cleanup_all()

    def test_very_long_signal_name(self):
        """Very long signal names should work."""
        backends = create_test_backends("edge_long")
        nodes, broadcast = create_router_nodes(backends)

        long_name = "A" * 200  # 200 character signal name

        config = f"""
test_workflow:
  LongNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: "{long_name}"
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert long_name in signals
        backends.cleanup_all()

    def test_signal_name_with_spaces(self):
        """Signal names with spaces work but are unusual."""
        backends = create_test_backends("edge_spaces")
        nodes, broadcast = create_router_nodes(backends)

        config = """
test_workflow:
  SpaceNode:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: "SIGNAL WITH SPACES"
"""
        exec_id = orchestrate(
            config=config,
            initial_workflow_name="test_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, exec_id)
        assert "SIGNAL WITH SPACES" in signals
        backends.cleanup_all()
