"""
Guide Chapter 4: Tool Nodes

This test demonstrates Tool nodes - direct function execution without LLM.
Tool nodes are the simplest way to integrate external functions into workflows.

Learning Goals:
- Understanding node_type: tool
- Configuring tool_name and tools_registry
- Understanding input_fields and context_parameter_field
- Understanding event_emissions with optional conditions
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_tool_nodes, extract_signals
from tests.test_cases.workflows.guide_tool import (
    tool_simple,
    tool_with_routing,
    tool_chain,
    tool_result_and_context_conditions,
    tool_inline_parameters,
    tool_inline_parameters_jinja,
)

# --- Tool Definitions ---

def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email (stub for testing)."""
    return {"status": "sent", "to": to, "subject": subject}


def process_payment(amount: float, currency: str) -> dict:
    """Process a payment (stub for testing)."""
    if amount <= 0:
        raise ValueError("Invalid amount")
    return {"status": "success", "amount": amount, "currency": currency}


def send_receipt(status: str, amount: float, currency: str) -> dict:
    """Send a receipt after successful payment."""
    return {"receipt_id": "REC-12345", "amount": amount}


def fetch_data(query: str) -> dict:
    """Fetch data from a source."""
    return {"data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]}


def transform_data(data: list) -> dict:
    """Transform raw data."""
    return {"transformed": [item["name"] for item in data]}


def process_payment_with_status(amount: float, currency: str) -> dict:
    """Process a payment and return status."""
    return {"status": "approved", "amount": amount, "currency": currency}


# --- Tests ---

def test_simple_tool_execution():
    """
    Tool node executes a function and emits success signal.
    """
    backends = create_test_backends("tool_simple")

    tools_registry = {
        "send_email": send_email,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=tool_simple,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "email_data": {
                "to": "user@example.com",
                "subject": "Hello",
                "body": "Test email body"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool output stored in output_field
    assert context["email_result"][-1]["status"] == "sent"
    assert context["email_result"][-1]["to"] == "user@example.com"
    assert "EMAIL_SENT" in signals

    backends.cleanup_all()


def test_tool_failure_routing():
    """
    Tool node emits failure signal when the function raises an exception.
    Uses registry's failure_signal for error handling.
    """
    backends = create_test_backends("tool_failure")

    tools_registry = {
        "process_payment": {
            "function": process_payment,
            "failure_signal": "PAYMENT_FAILED",
        },
        "send_receipt": send_receipt,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=tool_with_routing,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "payment_data": {
                "amount": -100,  # Invalid amount will cause failure
                "currency": "USD"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Failure path was taken
    assert "PAYMENT_FAILED" in signals
    # Success path was NOT taken
    assert "PAYMENT_SUCCESS" not in signals
    assert "RECEIPT_SENT" not in signals
    # Error message stored in output_field
    assert "Invalid amount" in context["payment_result"][-1]

    backends.cleanup_all()


def test_tool_chain():
    """
    Multiple tool nodes execute in sequence, passing data through context.
    """
    backends = create_test_backends("tool_chain")

    tools_registry = {
        "fetch_data": fetch_data,
        "transform_data": transform_data,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=tool_chain,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "query": {"query": "SELECT * FROM items"}
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Both tools executed
    assert "DATA_FETCHED" in signals
    assert "DATA_TRANSFORMED" in signals

    # Data flowed through the chain
    assert "raw_data" in context
    assert "transformed_data" in context
    assert context["transformed_data"][-1]["transformed"] == ["Item 1", "Item 2"]

    backends.cleanup_all()


def test_tool_conditions_with_result_and_context():
    """
    Tool conditions can reference both `result` (tool output) and `context` (workflow state).
    This allows conditional signal emission based on combination of tool output and existing context.
    """
    backends = create_test_backends("tool_result_context_conditions")

    tools_registry = {
        "process_payment": process_payment_with_status,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    # Test: VIP customer with large payment
    execution_id = orchestrate(
        config=tool_result_and_context_conditions,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "payment_data": {
                "amount": 5000,  # Large payment > 1000
                "currency": "USD"
            },
            "customer": {
                "is_vip": True,
                "name": "Premium Customer"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # All three conditions should match:
    # - result.status == 'approved' -> PAYMENT_SUCCESS
    # - result.status == 'approved' and context.customer.is_vip -> VIP_PAYMENT_SUCCESS
    # - result.status == 'approved' and context.payment_data.amount > 1000 -> LARGE_PAYMENT_SUCCESS
    assert "PAYMENT_SUCCESS" in signals
    assert "VIP_PAYMENT_SUCCESS" in signals
    assert "LARGE_PAYMENT_SUCCESS" in signals

    backends.cleanup_all()


def test_tool_conditions_context_not_matching():
    """
    Tool conditions using context only emit when both result AND context match.
    """
    backends = create_test_backends("tool_context_not_matching")

    tools_registry = {
        "process_payment": process_payment_with_status,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    # Test: Non-VIP customer with small payment
    execution_id = orchestrate(
        config=tool_result_and_context_conditions,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "payment_data": {
                "amount": 50,  # Small payment <= 1000
                "currency": "USD"
            },
            "customer": {
                "is_vip": False,  # Not VIP
                "name": "Regular Customer"
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # Only basic success should match (result.status == 'approved')
    assert "PAYMENT_SUCCESS" in signals
    # Context-based conditions should NOT match
    assert "VIP_PAYMENT_SUCCESS" not in signals
    assert "LARGE_PAYMENT_SUCCESS" not in signals

    backends.cleanup_all()


def soe_explore_docs(path: str, action: str) -> dict:
    """Stub for soe_explore_docs tool."""
    return {"content": f"Documentation content from {path}", "action": action}


def fetch_data_by_user(user_id: str, include_history: bool) -> dict:
    """Stub for fetch_data tool with user parameters."""
    return {
        "user_id": user_id,
        "include_history": include_history,
        "data": {"name": "Test User", "email": "test@example.com"}
    }


def test_tool_inline_parameters():
    """
    Tool node with inline parameters (static values defined in YAML).
    Parameters are passed directly without needing context_parameter_field.
    """
    backends = create_test_backends("tool_inline_params")

    tools_registry = {
        "soe_explore_docs": soe_explore_docs,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=tool_inline_parameters,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},  # No context needed - params are inline
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool executed with inline parameters
    assert "DOCS_READY" in signals
    assert "tool_documentation" in context
    assert "guide_01_tool.md" in context["tool_documentation"][-1]["content"]
    assert context["tool_documentation"][-1]["action"] == "read"

    backends.cleanup_all()


def test_tool_inline_parameters_with_jinja():
    """
    Tool node with inline parameters that use Jinja templates.
    Jinja templates in parameters are evaluated against context.
    """
    backends = create_test_backends("tool_inline_params_jinja")

    tools_registry = {
        "fetch_data": fetch_data_by_user,
    }

    nodes, broadcast_signals_caller = create_tool_nodes(backends, tools_registry)

    execution_id = orchestrate(
        config=tool_inline_parameters_jinja,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "current_user_id": "user_12345"  # This will be templated into parameters
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Tool executed with Jinja-templated parameters
    assert "DATA_FETCHED" in signals
    assert "user_data" in context
    # Jinja template was resolved from context
    assert context["user_data"][-1]["user_id"] == "user_12345"
    # Static boolean was passed through
    assert context["user_data"][-1]["include_history"] is True

    backends.cleanup_all()
