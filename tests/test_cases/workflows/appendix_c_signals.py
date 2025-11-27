"""
Workflow definitions for Appendix C: Signals Reference

These workflows demonstrate signal emission patterns:
1. Unconditional signals (no condition)
2. Jinja conditions (programmatic)
3. Plain text conditions (LLM selection)
4. Failure signals (error handling)
5. Tool result conditions
6. Sub-orchestration signals
"""

# =============================================================================
# UNCONDITIONAL SIGNALS
# =============================================================================

# Signals without conditions always emit (Router nodes)
# For Router nodes, ALL signals without conditions emit simultaneously
UNCONDITIONAL_SIGNALS = """
example_workflow:
  TriggerMultiple:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PROCESSING_DONE
      - signal_name: LOG_EVENT
"""

# =============================================================================
# JINJA CONDITIONS (Programmatic)
# =============================================================================

# Router with Jinja conditions - always programmatic
ROUTER_JINJA_CONDITIONS = """
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: HAS_DATA
        condition: "{{ context.data is defined and context.data }}"
      - signal_name: NO_DATA
        condition: "{{ context.data is not defined or not context.data }}"

  ProcessData:
    node_type: router
    event_triggers: [HAS_DATA]
    event_emissions:
      - signal_name: DONE

  HandleMissing:
    node_type: router
    event_triggers: [NO_DATA]
    event_emissions:
      - signal_name: DONE
"""

# LLM with Jinja conditions - programmatic, no LLM selection
LLM_JINJA_CONDITIONS = """
example_workflow:
  AnalyzeAndRoute:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: {{ context.text }}"
    output_field: analysis
    event_emissions:
      - signal_name: HIGH_PRIORITY
        condition: "{{ context.priority > 5 }}"
      - signal_name: NORMAL_PRIORITY
        condition: "{{ context.priority <= 5 }}"
"""

# =============================================================================
# PLAIN TEXT CONDITIONS (LLM Selection)
# =============================================================================

# LLM selects signal based on semantic understanding
LLM_SEMANTIC_SELECTION = """
example_workflow:
  SentimentRouter:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze the sentiment of this message: {{ context.message }}"
    output_field: sentiment_analysis
    event_emissions:
      - signal_name: POSITIVE_SENTIMENT
        condition: "The message expresses happiness, satisfaction, or positive emotions"
      - signal_name: NEGATIVE_SENTIMENT
        condition: "The message expresses anger, frustration, or negative emotions"
      - signal_name: NEUTRAL_SENTIMENT
        condition: "The message is factual, neutral, or emotionally ambiguous"
"""

# Agent with semantic signal selection
AGENT_SEMANTIC_SELECTION = """
example_workflow:
  TaskAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Help the user with their request: {{ context.request }}"
    available_tools: [search, calculate]
    output_field: result
    event_emissions:
      - signal_name: TASK_COMPLETED
        condition: "The task was successfully completed with a satisfactory result"
      - signal_name: TASK_FAILED
        condition: "The task could not be completed due to limitations or errors"
      - signal_name: TASK_NEEDS_CLARIFICATION
        condition: "The request is ambiguous and needs more information from the user"
"""

# =============================================================================
# FAILURE SIGNALS
# =============================================================================

# LLM with failure signal for error handling
LLM_FAILURE_SIGNAL = """
example_workflow:
  RiskyLLMCall:
    node_type: llm
    event_triggers: [START]
    prompt: "Generate a complex response for: {{ context.input }}"
    output_field: response
    retries: 2
    llm_failure_signal: LLM_FAILED
    event_emissions:
      - signal_name: SUCCESS

  HandleSuccess:
    node_type: router
    event_triggers: [SUCCESS]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

  HandleFailure:
    node_type: router
    event_triggers: [LLM_FAILED]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE
"""

# Agent with failure signal
AGENT_FAILURE_SIGNAL = """
example_workflow:
  ComplexAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Complete this complex task: {{ context.task }}"
    available_tools: [search]
    output_field: result
    retries: 1
    llm_failure_signal: AGENT_EXHAUSTED
    event_emissions:
      - signal_name: TASK_DONE

  OnSuccess:
    node_type: router
    event_triggers: [TASK_DONE]
    event_emissions:
      - signal_name: DONE

  OnFailure:
    node_type: router
    event_triggers: [AGENT_EXHAUSTED]
    event_emissions:
      - signal_name: DONE
"""

# Tool with failure signal (configured in registry, not YAML)
# The workflow just defines the node; failure_signal is in tools_registry
TOOL_FAILURE_SIGNAL = """
example_workflow:
  CallExternalAPI:
    node_type: tool
    event_triggers: [START]
    tool_name: flaky_api
    context_parameter_field: api_params
    output_field: api_result
    event_emissions:
      - signal_name: API_SUCCESS

  OnSuccess:
    node_type: router
    event_triggers: [API_SUCCESS]
    event_emissions:
      - signal_name: DONE

  OnFailure:
    node_type: router
    event_triggers: [API_FAILED]
    event_emissions:
      - signal_name: DONE
"""

# =============================================================================
# TOOL RESULT CONDITIONS
# =============================================================================

# Tool with result-based conditions
TOOL_RESULT_CONDITIONS = """
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_APPROVED
        condition: "{{ result.status == 'approved' }}"
      - signal_name: PAYMENT_DECLINED
        condition: "{{ result.status == 'declined' }}"
      - signal_name: PAYMENT_PENDING
        condition: "{{ result.status == 'pending' }}"

  OnApproved:
    node_type: router
    event_triggers: [PAYMENT_APPROVED]
    event_emissions:
      - signal_name: DONE

  OnDeclined:
    node_type: router
    event_triggers: [PAYMENT_DECLINED]
    event_emissions:
      - signal_name: DONE

  OnPending:
    node_type: router
    event_triggers: [PAYMENT_PENDING]
    event_emissions:
      - signal_name: DONE
"""

# Tool with combined result and context conditions
TOOL_RESULT_AND_CONTEXT = """
example_workflow:
  CheckOrder:
    node_type: tool
    event_triggers: [START]
    tool_name: validate_order
    context_parameter_field: order
    output_field: validation
    event_emissions:
      - signal_name: VIP_LARGE_ORDER
        condition: "{{ result.valid and context.customer.is_vip and context.order.total > 1000 }}"
      - signal_name: VIP_ORDER
        condition: "{{ result.valid and context.customer.is_vip }}"
      - signal_name: LARGE_ORDER
        condition: "{{ result.valid and context.order.total > 1000 }}"
      - signal_name: STANDARD_ORDER
        condition: "{{ result.valid }}"
      - signal_name: INVALID_ORDER
        condition: "{{ not result.valid }}"
"""

# =============================================================================
# SUB-ORCHESTRATION SIGNALS
# =============================================================================

# Parent workflow with signals_to_parent
PARENT_WITH_CHILD = """
parent_workflow:
  StartAnalysis:
    node_type: child
    event_triggers: [START]
    child_workflow_name: analysis_child
    child_initial_signals: [BEGIN]
    input_fields: [data_to_analyze]
    signals_to_parent: [ANALYSIS_SUCCESS, ANALYSIS_FAILED]
    context_updates_to_parent: [analysis_result]

  OnSuccess:
    node_type: router
    event_triggers: [ANALYSIS_SUCCESS]
    event_emissions:
      - signal_name: PARENT_DONE

  OnFailure:
    node_type: router
    event_triggers: [ANALYSIS_FAILED]
    event_emissions:
      - signal_name: PARENT_DONE

analysis_child:
  Analyze:
    node_type: llm
    event_triggers: [BEGIN]
    prompt: "Analyze this data: {{ context.data_to_analyze }}"
    output_field: analysis_result
    event_emissions:
      - signal_name: ANALYSIS_SUCCESS
        condition: "Analysis completed successfully"
      - signal_name: ANALYSIS_FAILED
        condition: "Analysis could not be completed"
"""

# =============================================================================
# EXCLUSIVE VS FAN-OUT PATTERNS
# =============================================================================

# Exclusive routing - only one path taken
EXCLUSIVE_ROUTING = """
example_workflow:
  RouteByType:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: TYPE_A
        condition: "{{ context.type == 'a' }}"
      - signal_name: TYPE_B
        condition: "{{ context.type == 'b' }}"
      - signal_name: TYPE_DEFAULT
        condition: "{{ context.type not in ['a', 'b'] }}"

  HandleA:
    node_type: router
    event_triggers: [TYPE_A]
    event_emissions:
      - signal_name: DONE

  HandleB:
    node_type: router
    event_triggers: [TYPE_B]
    event_emissions:
      - signal_name: DONE

  HandleDefault:
    node_type: router
    event_triggers: [TYPE_DEFAULT]
    event_emissions:
      - signal_name: DONE
"""

# Fan-out - multiple signals can emit simultaneously
FAN_OUT_SIGNALS = """
example_workflow:
  TriggerMultiple:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: NOTIFY_USER
        condition: "{{ context.notify_user }}"
      - signal_name: LOG_EVENT
        condition: "{{ context.log_enabled }}"
      - signal_name: UPDATE_METRICS

  NotifyUser:
    node_type: router
    event_triggers: [NOTIFY_USER]
    event_emissions:
      - signal_name: NOTIFICATION_SENT

  LogEvent:
    node_type: router
    event_triggers: [LOG_EVENT]
    event_emissions:
      - signal_name: EVENT_LOGGED

  UpdateMetrics:
    node_type: router
    event_triggers: [UPDATE_METRICS]
    event_emissions:
      - signal_name: METRICS_UPDATED
"""

# =============================================================================
# COMPLETE EXAMPLE: COMBINING ALL PATTERNS
# =============================================================================

# A comprehensive workflow showing multiple signal patterns
# Note: Use bracket notation for dict keys that conflict with dict methods (like 'items')
COMPREHENSIVE_SIGNAL_EXAMPLE = """
order_processing:
  # 1. Router with Jinja conditions (programmatic)
  ValidateOrder:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ORDER_VALID
        condition: "{{ context.order['line_items']|length > 0 and context.order.total > 0 }}"
      - signal_name: ORDER_INVALID
        condition: "{{ context.order['line_items']|length == 0 or context.order.total <= 0 }}"

  # 2. Tool with result conditions
  ProcessPayment:
    node_type: tool
    event_triggers: [ORDER_VALID]
    tool_name: charge_card
    context_parameter_field: payment_info
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS
        condition: "{{ result.charged == true }}"
      - signal_name: PAYMENT_FAILED
        condition: "{{ result.charged == false }}"

  # 3. LLM with failure signal and unconditional emission
  GenerateConfirmation:
    node_type: llm
    event_triggers: [PAYMENT_SUCCESS]
    prompt: "Generate a friendly order confirmation for order #{{ context.order.id }}"
    output_field: confirmation_message
    retries: 2
    llm_failure_signal: CONFIRMATION_FAILED
    event_emissions:
      - signal_name: ORDER_COMPLETE

  # 4. Fan-out: notify multiple systems
  NotifySystems:
    node_type: router
    event_triggers: [ORDER_COMPLETE]
    event_emissions:
      - signal_name: NOTIFY_CUSTOMER
      - signal_name: UPDATE_INVENTORY
      - signal_name: LOG_ORDER

  # Handle failures
  HandleInvalidOrder:
    node_type: router
    event_triggers: [ORDER_INVALID]
    event_emissions:
      - signal_name: WORKFLOW_ERROR

  HandlePaymentFailed:
    node_type: router
    event_triggers: [PAYMENT_FAILED]
    event_emissions:
      - signal_name: WORKFLOW_ERROR

  HandleConfirmationFailed:
    node_type: router
    event_triggers: [CONFIRMATION_FAILED]
    event_emissions:
      - signal_name: ORDER_COMPLETE
"""
