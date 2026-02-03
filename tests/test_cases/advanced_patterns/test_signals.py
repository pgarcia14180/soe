"""
Tests for Appendix C: Signals Reference

These tests demonstrate signal emission patterns:
1. Unconditional signals (no condition)
2. Jinja conditions (programmatic)
3. Plain text conditions (LLM selection)
4. Failure signals (error handling)
5. Tool result conditions
6. Exclusive vs fan-out patterns
"""

import pytest
from soe import orchestrate
from tests.test_cases.lib import (
    create_test_backends,
    create_router_nodes,
    create_llm_nodes,
    create_tool_nodes,
    create_nodes,
    extract_signals,
    create_call_llm,
)
from tests.test_cases.workflows.appendix_c_signals import (
    UNCONDITIONAL_SIGNALS,
    ROUTER_JINJA_CONDITIONS,
    LLM_JINJA_CONDITIONS,
    LLM_SEMANTIC_SELECTION,
    LLM_FAILURE_SIGNAL,
    TOOL_FAILURE_SIGNAL,
    TOOL_RESULT_CONDITIONS,
    EXCLUSIVE_ROUTING,
    FAN_OUT_SIGNALS,
    COMPREHENSIVE_SIGNAL_EXAMPLE,
    LLM_MULTI_SIGNAL_SELECTION,
    LLM_ZERO_SIGNAL_SELECTION,
)


class TestUnconditionalSignals:
    """Signals without conditions always emit (for Router nodes).

    Note: For LLM/Agent nodes with multiple signals, the LLM selects which
    signal to emit. To emit multiple signals unconditionally, use a Router
    node or use Jinja conditions like {{ true }}.
    """

    def test_router_unconditional_signals_all_emit(self):
        """
        Router nodes emit ALL signals that have no condition or truthy condition.
        This is the "unconditional" pattern.
        """
        backends = create_test_backends("router_unconditional_signals")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=UNCONDITIONAL_SIGNALS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"data": "test data"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Both signals should emit (no conditions on router = always emit)
        assert "PROCESSING_DONE" in signals
        assert "LOG_EVENT" in signals

        backends.cleanup_all()


class TestJinjaConditions:
    """Jinja conditions are evaluated programmatically by SOE."""

    def test_router_jinja_has_data(self):
        """Router emits HAS_DATA when data is defined."""
        backends = create_test_backends("router_jinja_has_data")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=ROUTER_JINJA_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"data": "some data"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "HAS_DATA" in signals
        assert "NO_DATA" not in signals
        assert "DONE" in signals

        backends.cleanup_all()

    def test_router_jinja_no_data(self):
        """Router emits NO_DATA when data is missing."""
        backends = create_test_backends("router_jinja_no_data")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=ROUTER_JINJA_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},  # No data
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "NO_DATA" in signals
        assert "HAS_DATA" not in signals
        assert "DONE" in signals

        backends.cleanup_all()

    def test_llm_jinja_high_priority(self):
        """LLM with Jinja conditions evaluates programmatically (no LLM selection)."""
        def stub_llm(prompt, config):
            return '{"analysis": "analyzed"}'

        backends = create_test_backends("llm_jinja_high")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_JINJA_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"text": "analyze this", "priority": 8},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Jinja evaluated: priority > 5 is true
        assert "HIGH_PRIORITY" in signals
        assert "NORMAL_PRIORITY" not in signals

        backends.cleanup_all()

    def test_llm_jinja_normal_priority(self):
        """LLM Jinja condition evaluates low priority correctly."""
        def stub_llm(prompt, config):
            return '{"analysis": "analyzed"}'

        backends = create_test_backends("llm_jinja_normal")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_JINJA_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"text": "analyze this", "priority": 3},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Jinja evaluated: priority <= 5 is true
        assert "NORMAL_PRIORITY" in signals
        assert "HIGH_PRIORITY" not in signals

        backends.cleanup_all()


class TestSemanticSelection:
    """Plain text conditions trigger LLM signal selection."""

    def test_llm_selects_positive_sentiment(self):
        """LLM selects POSITIVE_SENTIMENT based on semantic understanding."""
        def stub_llm(prompt, config):
            # LLM sees signal options and selects one (as list)
            return '{"sentiment_analysis": "The message is happy", "selected_signals": ["POSITIVE_SENTIMENT"]}'

        backends = create_test_backends("semantic_positive")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_SEMANTIC_SELECTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"message": "I love this product!"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "POSITIVE_SENTIMENT" in signals
        assert "NEGATIVE_SENTIMENT" not in signals
        assert "NEUTRAL_SENTIMENT" not in signals

        backends.cleanup_all()

    def test_llm_selects_negative_sentiment(self):
        """LLM selects NEGATIVE_SENTIMENT based on semantic understanding."""
        def stub_llm(prompt, config):
            return '{"sentiment_analysis": "The message is angry", "selected_signals": ["NEGATIVE_SENTIMENT"]}'

        backends = create_test_backends("semantic_negative")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_SEMANTIC_SELECTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"message": "This is terrible!"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "NEGATIVE_SENTIMENT" in signals

        backends.cleanup_all()


class TestFailureSignals:
    """Failure signals emit when LLM/Agent fails.

    Note: The `retries` field controls validation retries (JSON parsing, schema).
    LLM exceptions (network errors, API failures) are caught by the factory
    and immediately emit the failure signal without retries.
    """

    def test_llm_failure_signal_on_exception(self):
        """
        When LLM throws an exception, llm_failure_signal is emitted.
        Exceptions are not retried - they emit failure signal immediately.
        """
        def failing_llm(prompt, config):
            raise Exception("LLM unavailable")

        backends = create_test_backends("llm_failure")
        call_llm = create_call_llm(stub=failing_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_FAILURE_SIGNAL,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input": "test"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Failure signal should be emitted
        assert "LLM_FAILED" in signals
        # Success signal should NOT be emitted
        assert "SUCCESS" not in signals
        # Workflow should complete via failure handler
        assert "WORKFLOW_COMPLETE" in signals

        backends.cleanup_all()

    def test_llm_success_no_failure_signal(self):
        """When LLM succeeds, normal signals emit (not failure signal)."""
        def stub_llm(prompt, config):
            return '{"response": "success"}'

        backends = create_test_backends("llm_success")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_FAILURE_SIGNAL,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input": "test"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "SUCCESS" in signals
        assert "LLM_FAILED" not in signals
        assert "WORKFLOW_COMPLETE" in signals

        backends.cleanup_all()

    def test_tool_failure_signal_on_exception(self):
        """
        When a tool throws an exception and exhausts retries,
        the failure_signal from the registry is emitted.

        Note: Tool failure signals are configured in the tools_registry,
        not in the YAML workflow definition.
        """
        def flaky_api(request_id):
            raise Exception("API unavailable")

        backends = create_test_backends("tool_failure")
        # Configure failure_signal in the registry
        tools_registry = {
            "flaky_api": {
                "function": flaky_api,
                "max_retries": 2,
                "failure_signal": "API_FAILED",
            }
        }
        nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

        execution_id = orchestrate(
            config=TOOL_FAILURE_SIGNAL,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"api_params": {"request_id": "req_123"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Failure signal should be emitted
        assert "API_FAILED" in signals
        # Success signal should NOT be emitted
        assert "API_SUCCESS" not in signals
        # Workflow should complete via failure handler
        assert "DONE" in signals

        backends.cleanup_all()

    def test_tool_success_no_failure_signal(self):
        """When tool succeeds, normal signals emit (not failure signal)."""
        def flaky_api(request_id):
            return {"status": "ok", "data": "response"}

        backends = create_test_backends("tool_success")
        tools_registry = {
            "flaky_api": {
                "function": flaky_api,
                "max_retries": 2,
                "failure_signal": "API_FAILED",
            }
        }
        nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

        execution_id = orchestrate(
            config=TOOL_FAILURE_SIGNAL,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"api_params": {"request_id": "req_123"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "API_SUCCESS" in signals
        assert "API_FAILED" not in signals
        assert "DONE" in signals

        backends.cleanup_all()


class TestToolResultConditions:
    """Tool conditions can access both `result` and `context`."""

    def test_tool_result_approved(self):
        """Tool emits PAYMENT_APPROVED when result.status == 'approved'."""
        def process_payment(amount, card_number):
            return {"status": "approved", "transaction_id": "txn_123"}

        backends = create_test_backends("tool_approved")
        tools_registry = {"process_payment": process_payment}
        nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

        execution_id = orchestrate(
            config=TOOL_RESULT_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"payment_data": {"amount": 100, "card_number": "4111"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PAYMENT_APPROVED" in signals
        assert "PAYMENT_DECLINED" not in signals
        assert "PAYMENT_PENDING" not in signals
        assert "DONE" in signals

        backends.cleanup_all()

    def test_tool_result_declined(self):
        """Tool emits PAYMENT_DECLINED when result.status == 'declined'."""
        def process_payment(amount, card_number):
            return {"status": "declined", "reason": "insufficient funds"}

        backends = create_test_backends("tool_declined")
        tools_registry = {"process_payment": process_payment}
        nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

        execution_id = orchestrate(
            config=TOOL_RESULT_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"payment_data": {"amount": 100, "card_number": "4111"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PAYMENT_DECLINED" in signals
        assert "PAYMENT_APPROVED" not in signals
        assert "DONE" in signals

        backends.cleanup_all()

    def test_tool_result_pending(self):
        """Tool emits PAYMENT_PENDING when result.status == 'pending'."""
        def process_payment(amount, card_number):
            return {"status": "pending", "review_id": "rev_456"}

        backends = create_test_backends("tool_pending")
        tools_registry = {"process_payment": process_payment}
        nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

        execution_id = orchestrate(
            config=TOOL_RESULT_CONDITIONS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"payment_data": {"amount": 100, "card_number": "4111"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PAYMENT_PENDING" in signals
        assert "DONE" in signals

        backends.cleanup_all()


class TestExclusiveRouting:
    """Exclusive routing - only one path taken based on condition."""

    def test_exclusive_type_a(self):
        """Only TYPE_A signal emits when type == 'a'."""
        backends = create_test_backends("exclusive_a")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=EXCLUSIVE_ROUTING,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"type": "a"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "TYPE_A" in signals
        assert "TYPE_B" not in signals
        assert "TYPE_DEFAULT" not in signals
        assert "DONE" in signals

        backends.cleanup_all()

    def test_exclusive_type_default(self):
        """TYPE_DEFAULT emits when type is neither 'a' nor 'b'."""
        backends = create_test_backends("exclusive_default")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=EXCLUSIVE_ROUTING,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"type": "unknown"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "TYPE_DEFAULT" in signals
        assert "TYPE_A" not in signals
        assert "TYPE_B" not in signals
        assert "DONE" in signals

        backends.cleanup_all()


class TestFanOutSignals:
    """Fan-out - multiple signals can emit simultaneously."""

    def test_fan_out_all_conditions_true(self):
        """Multiple signals emit when their conditions are all true."""
        backends = create_test_backends("fan_out_all")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=FAN_OUT_SIGNALS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"notify_user": True, "log_enabled": True},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # All three signals should emit
        assert "NOTIFY_USER" in signals
        assert "LOG_EVENT" in signals
        assert "UPDATE_METRICS" in signals  # No condition = always emits
        # All handlers should run
        assert "NOTIFICATION_SENT" in signals
        assert "EVENT_LOGGED" in signals
        assert "METRICS_UPDATED" in signals

        backends.cleanup_all()

    def test_fan_out_partial_conditions(self):
        """Only matching conditions emit their signals."""
        backends = create_test_backends("fan_out_partial")
        nodes, broadcast_signals_caller = create_router_nodes(backends)

        execution_id = orchestrate(
            config=FAN_OUT_SIGNALS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"notify_user": False, "log_enabled": True},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Only LOG_EVENT and UPDATE_METRICS (no condition)
        assert "NOTIFY_USER" not in signals
        assert "LOG_EVENT" in signals
        assert "UPDATE_METRICS" in signals
        # Only matching handlers run
        assert "NOTIFICATION_SENT" not in signals
        assert "EVENT_LOGGED" in signals
        assert "METRICS_UPDATED" in signals

        backends.cleanup_all()


class TestComprehensiveExample:
    """Test the comprehensive workflow combining multiple signal patterns."""

    def test_successful_order_flow(self):
        """
        Complete flow: validation → payment → confirmation → notifications.
        Demonstrates: Jinja conditions, tool result, failure signal, fan-out.
        """
        def charge_card(amount, card_number):
            return {"charged": True, "transaction_id": "txn_789"}

        def stub_llm(prompt, config):
            return '{"confirmation_message": "Thank you for your order!"}'

        backends = create_test_backends("comprehensive_success")
        call_llm = create_call_llm(stub=stub_llm)
        tools_registry = {"charge_card": charge_card}
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=COMPREHENSIVE_SIGNAL_EXAMPLE,
            initial_workflow_name="order_processing",
            initial_signals=["START"],
            initial_context={
                "order": {"id": "ORD-001", "line_items": ["item1"], "total": 99.99},
                "payment_info": {"amount": 99.99, "card_number": "4111"},
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Validation passed
        assert "ORDER_VALID" in signals
        assert "ORDER_INVALID" not in signals

        # Payment succeeded
        assert "PAYMENT_SUCCESS" in signals
        assert "PAYMENT_FAILED" not in signals

        # Confirmation generated
        assert "ORDER_COMPLETE" in signals

        # Fan-out: all notifications triggered
        assert "NOTIFY_CUSTOMER" in signals
        assert "UPDATE_INVENTORY" in signals
        assert "LOG_ORDER" in signals

        backends.cleanup_all()

    def test_invalid_order_flow(self):
        """Invalid order triggers ORDER_INVALID and skips payment.

        Note: This test only runs the validation step (Router node),
        so we only need router nodes. The workflow will stop at
        HandleInvalidOrder since there's no Tool or LLM node handler.
        """
        # For invalid order, we only hit Router nodes
        # But we need tools_registry for the Tool node definition to be valid
        def charge_card(amount, card_number):
            return {"charged": False}

        def stub_llm(prompt, config):
            return '{"confirmation_message": "Thanks!"}'

        backends = create_test_backends("comprehensive_invalid")
        call_llm = create_call_llm(stub=stub_llm)
        tools_registry = {"charge_card": charge_card}
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=COMPREHENSIVE_SIGNAL_EXAMPLE,
            initial_workflow_name="order_processing",
            initial_signals=["START"],
            initial_context={
                "order": {"id": "ORD-002", "line_items": [], "total": 0},  # Invalid
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "ORDER_INVALID" in signals
        assert "ORDER_VALID" not in signals
        assert "WORKFLOW_ERROR" in signals
        # Should not reach payment or confirmation
        assert "PAYMENT_SUCCESS" not in signals
        assert "ORDER_COMPLETE" not in signals

        backends.cleanup_all()

    def test_payment_failed_flow(self):
        """Payment failure triggers PAYMENT_FAILED and error handling."""
        def charge_card(amount, card_number):
            return {"charged": False, "error": "Card declined"}

        def stub_llm(prompt, config):
            return '{"confirmation_message": "Thanks!"}'

        backends = create_test_backends("comprehensive_payment_failed")
        call_llm = create_call_llm(stub=stub_llm)
        tools_registry = {"charge_card": charge_card}
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=COMPREHENSIVE_SIGNAL_EXAMPLE,
            initial_workflow_name="order_processing",
            initial_signals=["START"],
            initial_context={
                "order": {"id": "ORD-003", "line_items": ["item1"], "total": 99.99},
                "payment_info": {"amount": 99.99, "card_number": "0000"},
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "ORDER_VALID" in signals
        assert "PAYMENT_FAILED" in signals
        assert "PAYMENT_SUCCESS" not in signals
        assert "WORKFLOW_ERROR" in signals
        # Should not reach confirmation
        assert "ORDER_COMPLETE" not in signals

        backends.cleanup_all()


class TestMultiSignalSelection:
    """LLM can select multiple signals semantically in a single request."""

    def test_llm_selects_multiple_signals(self):
        """
        LLM selects multiple signals when multiple topics apply.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            # LLM determines both TOOL_DOCS and LLM_DOCS are relevant
            return '{"routing_analysis": "This question is about both tools and LLM nodes.", "selected_signals": ["NEED_TOOL_DOCS", "NEED_LLM_DOCS"]}'

        backends = create_test_backends("multi_signal_multiple")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_MULTI_SIGNAL_SELECTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"question": "How do I call a Python function from an LLM node?"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Both signals should be emitted
        assert "NEED_TOOL_DOCS" in signals
        assert "NEED_LLM_DOCS" in signals
        # Router not selected
        assert "NEED_ROUTER_DOCS" not in signals
        # Both handlers should have run
        assert signals.count("DOCS_FETCHED") == 2

        backends.cleanup_all()

    def test_llm_selects_single_signal(self):
        """
        LLM can still select just one signal when only one applies.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            return '{"routing_analysis": "This is only about routers.", "selected_signals": ["NEED_ROUTER_DOCS"]}'

        backends = create_test_backends("multi_signal_single")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_MULTI_SIGNAL_SELECTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"question": "How do conditional signals work in routers?"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Only router signal emitted
        assert "NEED_ROUTER_DOCS" in signals
        assert "NEED_TOOL_DOCS" not in signals
        assert "NEED_LLM_DOCS" not in signals

        backends.cleanup_all()

    def test_llm_selects_all_signals(self):
        """
        LLM can select all signals when all topics apply.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            return '{"routing_analysis": "This covers everything.", "selected_signals": ["NEED_TOOL_DOCS", "NEED_LLM_DOCS", "NEED_ROUTER_DOCS"]}'

        backends = create_test_backends("multi_signal_all")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_MULTI_SIGNAL_SELECTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"question": "Give me an overview of all node types"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # All three signals emitted
        assert "NEED_TOOL_DOCS" in signals
        assert "NEED_LLM_DOCS" in signals
        assert "NEED_ROUTER_DOCS" in signals
        # All handlers ran
        assert signals.count("DOCS_FETCHED") == 3

        backends.cleanup_all()

    def test_llm_selects_zero_signals(self):
        """
        LLM can select no signals when none apply - this is valid, not an error.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            # LLM determines neither condition applies
            return '{"categorization": "This is just a casual greeting.", "selected_signals": []}'

        backends = create_test_backends("multi_signal_zero")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

        execution_id = orchestrate(
            config=LLM_ZERO_SIGNAL_SELECTION,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"input": "Hello, how are you?"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # No signals selected - neither IS_URGENT nor IS_IMPORTANT
        assert "IS_URGENT" not in signals
        assert "IS_IMPORTANT" not in signals
        # Workflow completed without error (no DONE signal since no handler triggered)
        assert "DONE" not in signals

        backends.cleanup_all()
