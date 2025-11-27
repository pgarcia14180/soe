"""
Tests for Infrastructure Guardrail Patterns from Appendix A.

These tests verify the production-ready patterns:
- Execute Only Once
- Health Check Guardrail
- Rate Limiting
- Kill Switch
- Combined Production Guardrails
"""

from soe import orchestrate, broadcast_signals
from soe.lib.context_fields import set_field
from tests.test_cases.lib import (
    create_test_backends,
    create_nodes,
    setup_nodes,
    extract_signals,
    create_call_llm,
)
from tests.test_cases.workflows.appendix_a_operational import (
    EXECUTE_ONCE,
    HEALTH_CHECK_GUARDRAIL,
    RATE_LIMITING,
    KILL_SWITCH,
    PRODUCTION_GUARDRAILS,
)


# =============================================================================
# EXECUTE ONLY ONCE
# =============================================================================


class TestExecuteOnce:
    """Execute only once pattern - guardrail for idempotent operations."""

    def test_first_execution_proceeds(self):
        """First execution should proceed through the guardrail."""
        call_count = 0

        def expensive_api_call(key: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"status": "success", "key": key}

        tools_registry = {"expensive_api_call": expensive_api_call}
        backends = create_test_backends("execute_once_first")
        broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

        execution_id = orchestrate(
            config=EXECUTE_ONCE,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"api_params": {"key": "value"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)
        assert call_count == 1
        assert "OPERATION_COMPLETE" in signals

    def test_subsequent_triggers_skip(self):
        """Subsequent triggers should skip the expensive operation."""
        call_count = 0

        def expensive_api_call() -> dict:
            nonlocal call_count
            call_count += 1
            return {"status": "success"}

        tools_registry = {"expensive_api_call": expensive_api_call}
        backends = create_test_backends("execute_once_skip")
        nodes, broadcast_signals_caller = create_nodes(backends, tools_registry=tools_registry)

        # First execution
        execution_id = orchestrate(
            config=EXECUTE_ONCE,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"api_params": {}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )
        assert call_count == 1

        # Second trigger via RETRY_REQUEST - should skip
        broadcast_signals(execution_id, ["RETRY_REQUEST"], nodes, backends)

        signals = extract_signals(backends, execution_id)
        # Tool should NOT have been called again
        assert call_count == 1
        assert "ALREADY_EXECUTED" in signals


# =============================================================================
# HEALTH CHECK GUARDRAIL
# =============================================================================


class TestHealthCheckGuardrail:
    """Health check pattern - validate before expensive operations."""

    def test_healthy_service_proceeds(self):
        """When service is healthy, main process executes."""

        def check_service_health() -> dict:
            return {"is_healthy": True, "latency_ms": 50}

        def stub_llm(prompt: str, config: dict) -> str:
            return '{"result": "Processed successfully"}'

        tools_registry = {"check_service_health": check_service_health}
        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("health_check_healthy")
        broadcast_signals_caller = setup_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=HEALTH_CHECK_GUARDRAIL,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "test request"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)
        context = backends.context.get_context(execution_id)

        assert "SERVICE_HEALTHY" in signals
        assert "DONE" in signals
        assert "result" in context

    def test_unhealthy_service_fallback(self):
        """When service is unhealthy, fallback path is taken."""
        llm_call_count = 0

        def check_service_health() -> dict:
            return {"is_healthy": False, "error": "Connection timeout"}

        def stub_llm(prompt: str, config: dict) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return "Should not be called"

        tools_registry = {"check_service_health": check_service_health}
        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("health_check_unhealthy")
        broadcast_signals_caller = setup_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=HEALTH_CHECK_GUARDRAIL,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "test request"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "SERVICE_UNHEALTHY" in signals
        assert "DONE" in signals
        # LLM should NOT have been called
        assert llm_call_count == 0


# =============================================================================
# RATE LIMITING
# =============================================================================


class TestRateLimiting:
    """Rate limiting pattern - throttle based on execution count."""

    def test_under_limit_allowed(self):
        """Requests under rate limit should proceed."""
        call_count = 0

        def external_api() -> dict:
            nonlocal call_count
            call_count += 1
            return {"response": "ok"}

        tools_registry = {"external_api": external_api}
        backends = create_test_backends("rate_limit_under")
        broadcast_signals_caller = setup_nodes(backends, tools_registry=tools_registry)

        execution_id = orchestrate(
            config=RATE_LIMITING,
            initial_workflow_name="example_workflow",
            initial_signals=["REQUEST"],
            initial_context={"rate_limit": 5, "api_params": {}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert call_count == 1
        assert "ALLOWED" in signals
        assert "CALL_COMPLETE" in signals

    def test_at_limit_throttled(self):
        """Requests at or over rate limit should be throttled."""
        call_count = 0

        def external_api() -> dict:
            nonlocal call_count
            call_count += 1
            return {"response": "ok"}

        tools_registry = {"external_api": external_api}
        backends = create_test_backends("rate_limit_at")
        nodes, broadcast_signals_caller = create_nodes(backends, tools_registry=tools_registry)

        # First request - rate_limit=2
        execution_id = orchestrate(
            config=RATE_LIMITING,
            initial_workflow_name="example_workflow",
            initial_signals=["REQUEST"],
            initial_context={"rate_limit": 2, "api_params": {}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )
        assert call_count == 1

        # Second request - still under limit
        broadcast_signals(execution_id, ["REQUEST"], nodes, backends)
        assert call_count == 2

        # Third request - at limit, should be throttled
        broadcast_signals(execution_id, ["REQUEST"], nodes, backends)

        signals = extract_signals(backends, execution_id)

        # Call count should NOT increase past 2
        assert call_count == 2
        assert "RATE_LIMITED" in signals
        assert "THROTTLED" in signals


# =============================================================================
# KILL SWITCH
# =============================================================================


class TestKillSwitch:
    """Kill switch pattern - context-based execution suspension."""

    def test_without_kill_switch_executes(self):
        """Without kill switch set, execution proceeds."""

        def stub_llm(prompt: str, config: dict) -> str:
            return '{"step_result": "Step completed"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("kill_switch_off")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=KILL_SWITCH,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"current_step": "step1", "steps_remaining": 0},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "PROCEED" in signals
        assert "STEP_DONE" in signals
        assert "ALL_COMPLETE" in signals

    def test_with_kill_switch_suspends(self):
        """With kill switch set, execution is suspended."""
        llm_call_count = 0

        def stub_llm(prompt: str, config: dict) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return "Should not be called"

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("kill_switch_on")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=KILL_SWITCH,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "kill_switch": True,
                "current_step": "step1",
                "steps_remaining": 5,
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "SUSPENDED" in signals
        assert "AWAITING_RESUME" in signals
        # LLM should NOT have been called
        assert llm_call_count == 0

    def test_kill_switch_activated_mid_execution(self):
        """Kill switch can block subsequent requests after initial execution."""
        llm_call_count = 0

        def stub_llm(prompt: str, config: dict) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return '{"step_result": "Step done"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("kill_switch_mid")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        # Start workflow - completes one step then finishes (steps_remaining=0)
        execution_id = orchestrate(
            config=KILL_SWITCH,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={
                "current_step": "step1",
                "steps_remaining": 0,  # Completes after one step
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        # First step executed successfully
        assert llm_call_count == 1

        # Now activate kill switch and request another execution via START
        context = backends.context.get_context(execution_id)
        set_field(context, "kill_switch", True)
        set_field(context, "current_step", "step2")
        backends.context.save_context(execution_id, context)

        # Send START signal - should be blocked by kill switch
        broadcast_signals(execution_id, ["START"], nodes, backends)

        signals = extract_signals(backends, execution_id)

        # LLM should NOT have been called again - kill switch blocked it
        assert llm_call_count == 1
        assert "SUSPENDED" in signals
        assert "AWAITING_RESUME" in signals


# =============================================================================
# PRODUCTION GUARDRAILS (COMBINED)
# =============================================================================


class TestProductionGuardrails:
    """Combined guardrails pattern - kill switch + rate limit + health check."""

    def test_all_checks_pass(self):
        """When all guardrails pass, core operation executes."""

        def system_health_check() -> dict:
            return {"ready": True}

        def stub_llm(prompt: str, config: dict) -> str:
            return '{"result": "Processed successfully"}'

        tools_registry = {"system_health_check": system_health_check}
        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("production_all_pass")
        broadcast_signals_caller = setup_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=PRODUCTION_GUARDRAILS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "test", "system_suspended": False},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)
        context = backends.context.get_context(execution_id)

        assert "EXECUTE" in signals
        assert "DONE" in signals
        assert "result" in context

    def test_kill_switch_blocks(self):
        """Kill switch blocks execution before any other checks."""
        llm_call_count = 0

        def system_health_check() -> dict:
            return {"ready": True}

        def stub_llm(prompt: str, config: dict) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return "Should not be called"

        tools_registry = {"system_health_check": system_health_check}
        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("production_kill_switch")
        broadcast_signals_caller = setup_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=PRODUCTION_GUARDRAILS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "test", "system_suspended": True},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "SYSTEM_SUSPENDED" in signals
        assert "EXECUTE" not in signals
        assert llm_call_count == 0

    def test_unhealthy_system_blocks(self):
        """Unhealthy system blocks execution even if other checks pass."""
        llm_call_count = 0

        def system_health_check() -> dict:
            return {"ready": False, "reason": "Database unavailable"}

        def stub_llm(prompt: str, config: dict) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return "Should not be called"

        tools_registry = {"system_health_check": system_health_check}
        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("production_unhealthy")
        broadcast_signals_caller = setup_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=PRODUCTION_GUARDRAILS,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "test", "system_suspended": False},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "SYSTEM_DEGRADED" in signals
        assert "EXECUTE" not in signals
        assert llm_call_count == 0
