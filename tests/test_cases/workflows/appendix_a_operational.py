"""
Appendix A: Operational Features - workflow examples.

These workflows demonstrate operational context usage,
infrastructure configs (retries), and advanced patterns.
"""

# Operational context access - checking signals fired
OPERATIONAL_SIGNALS_CHECK = """
example_workflow:
  StartRouter:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INITIALIZED

  SignalChecker:
    node_type: router
    event_triggers: [INITIALIZED]
    event_emissions:
      - signal_name: ALL_SIGNALS_FIRED
        condition: "{{ 'START' in context.__operational__.signals and 'INITIALIZED' in context.__operational__.signals }}"
"""

# Wait for multiple signals (AND logic)
WAIT_FOR_MULTIPLE_SIGNALS = """
example_workflow:
  TaskA:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: A_DONE

  TaskB:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: B_DONE

  WaitForBoth:
    node_type: router
    event_triggers: [A_DONE, B_DONE]
    event_emissions:
      - signal_name: BOTH_COMPLETE
        condition: "{{ 'A_DONE' in context.__operational__.signals and 'B_DONE' in context.__operational__.signals }}"
      - signal_name: WAITING
        condition: "{{ not ('A_DONE' in context.__operational__.signals and 'B_DONE' in context.__operational__.signals) }}"
"""

# LLM call count check - limit AI usage
LLM_CALL_LIMIT = """
example_workflow:
  FirstLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "First task: {{ context.task }}"
    output_field: firstResult
    event_emissions:
      - signal_name: FIRST_DONE

  CheckLLMCount:
    node_type: router
    event_triggers: [FIRST_DONE]
    event_emissions:
      - signal_name: CONTINUE_LLM
        condition: "{{ context.__operational__.llm_calls < 3 }}"
      - signal_name: LLM_LIMIT_REACHED
        condition: "{{ context.__operational__.llm_calls >= 3 }}"

  SecondLLM:
    node_type: llm
    event_triggers: [CONTINUE_LLM]
    prompt: "Second task based on: {{ context.firstResult }}"
    output_field: secondResult
    event_emissions:
      - signal_name: SECOND_DONE
"""

# Tool call count check - limit tool usage
TOOL_CALL_LIMIT = """
example_workflow:
  FirstTool:
    node_type: tool
    event_triggers: [START]
    tool_name: api_call
    context_parameter_field: api_params
    output_field: firstResult
    event_emissions:
      - signal_name: FIRST_DONE

  CheckToolCount:
    node_type: router
    event_triggers: [FIRST_DONE]
    event_emissions:
      - signal_name: CONTINUE_TOOLS
        condition: "{{ context.__operational__.tool_calls < 10 }}"
      - signal_name: TOOL_LIMIT_REACHED
        condition: "{{ context.__operational__.tool_calls >= 10 }}"

  SecondTool:
    node_type: tool
    event_triggers: [CONTINUE_TOOLS]
    tool_name: api_call
    context_parameter_field: api_params
    output_field: secondResult
    event_emissions:
      - signal_name: SECOND_DONE
"""

# Error count check - circuit breaker pattern
ERROR_CIRCUIT_BREAKER = """
example_workflow:
  ProcessData:
    node_type: tool
    event_triggers: [START]
    tool_name: risky_operation
    context_parameter_field: data
    output_field: result
    event_emissions:
      - signal_name: SUCCESS

  CheckErrors:
    node_type: router
    event_triggers: [FAILURE]
    event_emissions:
      - signal_name: RETRY
        condition: "{{ context.__operational__.errors < 3 }}"
      - signal_name: CIRCUIT_OPEN
        condition: "{{ context.__operational__.errors >= 3 }}"

  RetryHandler:
    node_type: router
    event_triggers: [RETRY]
    event_emissions:
      - signal_name: START
"""

# Node execution count - prevent infinite loops
LOOP_PREVENTION = """
example_workflow:
  LoopingNode:
    node_type: router
    event_triggers: [START, CONTINUE]
    event_emissions:
      - signal_name: CONTINUE
        condition: "{{ context.__operational__.nodes.get('LoopingNode', 0) < 5 }}"
      - signal_name: LOOP_LIMIT_REACHED
        condition: "{{ context.__operational__.nodes.get('LoopingNode', 0) >= 5 }}"
"""

# LLM with retries config
LLM_WITH_RETRIES = """
example_workflow:
  ReliableLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: {{ context.input }}"
    output_field: result
    retries: 5
    event_emissions:
      - signal_name: DONE
"""

# LLM with failure signal
LLM_WITH_FAILURE_SIGNAL = """
example_workflow:
  LLMWithFallback:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: {{ context.input }}"
    output_field: result
    retries: 3
    llm_failure_signal: LLM_FAILED
    event_emissions:
      - signal_name: DONE

  HandleLLMFailure:
    node_type: router
    event_triggers: [LLM_FAILED]
    event_emissions:
      - signal_name: USE_FALLBACK
"""

# Agent with retries config
AGENT_WITH_RETRIES = """
example_workflow:
  ReliableAgent:
    node_type: agent
    event_triggers: [START]
    system_prompt: "You are a helpful assistant."
    user_prompt: "Help with: {{ context.request }}"
    output_field: response
    available_tools: [search]
    retries: 2
    event_emissions:
      - signal_name: AGENT_DONE
"""

# Agent with failure signals
AGENT_WITH_FAILURE_SIGNALS = """
example_workflow:
  RobustAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Complete the task: {{ context.task }}"
    tools: [risky_operation]
    output_field: result
    retries: 3
    llm_failure_signal: AGENT_EXHAUSTED
    event_emissions:
      - signal_name: DONE

  HandleAgentExhausted:
    node_type: router
    event_triggers: [AGENT_EXHAUSTED]
    event_emissions:
      - signal_name: FALLBACK_REQUIRED
"""

# Conditional LLM based on operational state
CONDITIONAL_LLM = """
example_workflow:
  CheckState:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: NEEDS_LLM
        condition: "{{ context.__operational__.llm_calls == 0 }}"
      - signal_name: USE_CACHED
        condition: "{{ context.__operational__.llm_calls > 0 }}"

  CallLLM:
    node_type: llm
    event_triggers: [NEEDS_LLM]
    prompt: "Process: {{ context.input }}"
    output_field: result
    event_emissions:
      - signal_name: COMPLETE

  UseCached:
    node_type: router
    event_triggers: [USE_CACHED]
    event_emissions:
      - signal_name: COMPLETE
"""


# =============================================================================
# INFRASTRUCTURE PATTERNS
# =============================================================================

# Execute Only Once - Guardrail router that checks if a node has already executed
EXECUTE_ONCE = """
example_workflow:
  OnceGuard:
    node_type: router
    event_triggers: [START, RETRY_REQUEST]
    event_emissions:
      - signal_name: PROCEED
        condition: "{{ context.__operational__.nodes.get('ExpensiveOperation', 0) == 0 }}"
      - signal_name: ALREADY_EXECUTED
        condition: "{{ context.__operational__.nodes.get('ExpensiveOperation', 0) > 0 }}"

  ExpensiveOperation:
    node_type: tool
    event_triggers: [PROCEED]
    tool_name: expensive_api_call
    context_parameter_field: api_params
    output_field: api_result
    event_emissions:
      - signal_name: OPERATION_COMPLETE

  SkipHandler:
    node_type: router
    event_triggers: [ALREADY_EXECUTED]
    event_emissions:
      - signal_name: OPERATION_COMPLETE
"""

# Health Check Guardrail - Router + Tool pattern for validation before proceeding
HEALTH_CHECK_GUARDRAIL = """
example_workflow:
  HealthCheckRouter:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHECK_SERVICE

  ServiceHealthCheck:
    node_type: tool
    event_triggers: [CHECK_SERVICE]
    tool_name: check_service_health
    output_field: health_status
    event_emissions:
      - signal_name: HEALTH_CHECKED

  HealthGuard:
    node_type: router
    event_triggers: [HEALTH_CHECKED]
    event_emissions:
      - signal_name: SERVICE_HEALTHY
        condition: "{{ context.health_status.is_healthy == true }}"
      - signal_name: SERVICE_UNHEALTHY
        condition: "{{ context.health_status.is_healthy != true }}"

  MainProcess:
    node_type: llm
    event_triggers: [SERVICE_HEALTHY]
    prompt: "Process with healthy service: {{ context.request }}"
    output_field: result
    event_emissions:
      - signal_name: DONE

  UnhealthyFallback:
    node_type: router
    event_triggers: [SERVICE_UNHEALTHY]
    event_emissions:
      - signal_name: DONE
"""

# Rate Limiting - Count executions and throttle
RATE_LIMITING = """
example_workflow:
  RateLimitGuard:
    node_type: router
    event_triggers: [REQUEST]
    event_emissions:
      - signal_name: ALLOWED
        condition: "{{ context.__operational__.nodes.get('APICall', 0) < context.rate_limit }}"
      - signal_name: RATE_LIMITED
        condition: "{{ context.__operational__.nodes.get('APICall', 0) >= context.rate_limit }}"

  APICall:
    node_type: tool
    event_triggers: [ALLOWED]
    tool_name: external_api
    context_parameter_field: api_params
    output_field: api_response
    event_emissions:
      - signal_name: CALL_COMPLETE

  RateLimitHandler:
    node_type: router
    event_triggers: [RATE_LIMITED]
    event_emissions:
      - signal_name: THROTTLED
"""

# Kill Switch - Context-based execution suspension
KILL_SWITCH = """
example_workflow:
  KillSwitchGuard:
    node_type: router
    event_triggers: [START, CONTINUE]
    event_emissions:
      - signal_name: PROCEED
        condition: "{{ context.kill_switch != true }}"
      - signal_name: SUSPENDED
        condition: "{{ context.kill_switch == true }}"

  MainProcess:
    node_type: llm
    event_triggers: [PROCEED]
    prompt: "Execute step: {{ context.current_step }}"
    output_field: step_result
    event_emissions:
      - signal_name: STEP_DONE

  NextStep:
    node_type: router
    event_triggers: [STEP_DONE]
    event_emissions:
      - signal_name: CONTINUE
        condition: "{{ context.steps_remaining > 0 }}"
      - signal_name: ALL_COMPLETE
        condition: "{{ context.steps_remaining <= 0 }}"

  SuspendHandler:
    node_type: router
    event_triggers: [SUSPENDED]
    event_emissions:
      - signal_name: AWAITING_RESUME
"""

# Combined Pattern - Kill switch with health check and rate limiting
PRODUCTION_GUARDRAILS = """
example_workflow:
  EntryGuard:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHECK_KILL_SWITCH

  KillSwitchCheck:
    node_type: router
    event_triggers: [CHECK_KILL_SWITCH]
    event_emissions:
      - signal_name: CHECK_RATE
        condition: "{{ context.system_suspended != true }}"
      - signal_name: SYSTEM_SUSPENDED
        condition: "{{ context.system_suspended == true }}"

  RateLimitCheck:
    node_type: router
    event_triggers: [CHECK_RATE]
    event_emissions:
      - signal_name: CHECK_HEALTH
        condition: "{{ context.__operational__.nodes.get('CoreOperation', 0) < 100 }}"
      - signal_name: RATE_EXCEEDED
        condition: "{{ context.__operational__.nodes.get('CoreOperation', 0) >= 100 }}"

  HealthCheck:
    node_type: tool
    event_triggers: [CHECK_HEALTH]
    tool_name: system_health_check
    output_field: system_health
    event_emissions:
      - signal_name: HEALTH_RESULT

  HealthDecision:
    node_type: router
    event_triggers: [HEALTH_RESULT]
    event_emissions:
      - signal_name: EXECUTE
        condition: "{{ context.system_health.ready == true }}"
      - signal_name: SYSTEM_DEGRADED
        condition: "{{ context.system_health.ready != true }}"

  CoreOperation:
    node_type: llm
    event_triggers: [EXECUTE]
    prompt: "Process: {{ context.request }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
"""
