"""
Workflow definitions for Router Nodes (formerly Guide Chapter 1: Basics)

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Router is one of the three core node types in SOE. It receives signals,
evaluates conditions, and emits new signals. No LLM or tool execution.
"""

# Simple router that validates input
simple_router_validation = """
example_workflow:
  InputValidator:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID_INPUT
        condition: "{{ context.user_input is defined and context.user_input != '' }}"
      - signal_name: INVALID_INPUT
        condition: "{{ context.user_input is not defined or context.user_input == '' }}"
"""

# Unconditional signal forwarding
simple_router_unconditional = """
example_workflow:
  Forwarder:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CONTINUE
"""

# ============================================================================
# EDGE CASE WORKFLOWS
# ============================================================================

# Edge case: Router with multiple triggers (responds to any of them)
router_multiple_triggers = """
example_workflow:
  MultiTrigger:
    node_type: router
    event_triggers: [START, RETRY, MANUAL]
    event_emissions:
      - signal_name: PROCESSED
"""

# Edge case: Router triggered by non-matching signal (should NOT execute)
router_no_matching_trigger = """
example_workflow:
  WaitsForDifferentSignal:
    node_type: router
    event_triggers: [SOMETHING_ELSE]
    event_emissions:
      - signal_name: SHOULD_NOT_EMIT
"""

# Edge case: Multiple conditions where ALL could be true
router_multiple_true_conditions = """
example_workflow:
  MultipleMatches:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: FIRST_MATCH
        condition: "{{ context.value > 5 }}"
      - signal_name: SECOND_MATCH
        condition: "{{ context.value > 10 }}"
"""

# Edge case: No conditions match (no signals should emit)
router_no_conditions_match = """
example_workflow:
  NoMatch:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: HIGH
        condition: "{{ context.value > 100 }}"
      - signal_name: LOW
        condition: "{{ context.value < 0 }}"
"""

# Edge case: Condition references undefined variable (should handle gracefully)
router_undefined_variable = """
example_workflow:
  UndefinedCheck:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: EXISTS
        condition: "{{ context.missing_field is defined }}"
      - signal_name: MISSING
        condition: "{{ context.missing_field is not defined }}"
"""

# Edge case: Multiple routers in sequence (chaining)
router_chain = """
example_workflow:
  FirstRouter:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: STEP_ONE_DONE

  SecondRouter:
    node_type: router
    event_triggers: [STEP_ONE_DONE]
    event_emissions:
      - signal_name: STEP_TWO_DONE

  ThirdRouter:
    node_type: router
    event_triggers: [STEP_TWO_DONE]
    event_emissions:
      - signal_name: ALL_DONE
"""

# Edge case: Complex Jinja2 expression
router_complex_condition = """
example_workflow:
  ComplexCheck:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PREMIUM_USER
        condition: "{{ context.user.tier == 'premium' and context.user.credits > 0 }}"
      - signal_name: FREE_USER
        condition: "{{ context.user.tier == 'free' or context.user.credits <= 0 }}"
"""

# Edge case: Boolean context values
router_boolean_context = """
example_workflow:
  BooleanCheck:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ENABLED
        condition: "{{ context.feature_enabled }}"
      - signal_name: DISABLED
        condition: "{{ not context.feature_enabled }}"
"""

# Edge case: Null/None value handling
router_null_handling = """
example_workflow:
  NullCheck:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: HAS_VALUE
        condition: "{{ context.nullable_field is not none and context.nullable_field != '' }}"
      - signal_name: NO_VALUE
        condition: "{{ context.nullable_field is none or context.nullable_field == '' }}"
"""

# ============================================================================
# DECISION TREE / GRAPH WORKFLOWS
# ============================================================================

# Decision tree: Routers that branch to other routers based on context
# This demonstrates how SOE workflows form a directed graph, not just linear chains
router_decision_tree = """
example_workflow:
  # Entry point: classify the request type
  RequestClassifier:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: HANDLE_ORDER
        condition: "{{ context.request_type == 'order' }}"
      - signal_name: HANDLE_SUPPORT
        condition: "{{ context.request_type == 'support' }}"
      - signal_name: HANDLE_UNKNOWN
        condition: "{{ context.request_type not in ['order', 'support'] }}"

  # Branch 1: Order handling - further classification
  OrderRouter:
    node_type: router
    event_triggers: [HANDLE_ORDER]
    event_emissions:
      - signal_name: NEW_ORDER
        condition: "{{ context.order_action == 'new' }}"
      - signal_name: CANCEL_ORDER
        condition: "{{ context.order_action == 'cancel' }}"
      - signal_name: TRACK_ORDER
        condition: "{{ context.order_action == 'track' }}"

  # Branch 2: Support handling - further classification
  SupportRouter:
    node_type: router
    event_triggers: [HANDLE_SUPPORT]
    event_emissions:
      - signal_name: BILLING_ISSUE
        condition: "{{ context.support_category == 'billing' }}"
      - signal_name: TECHNICAL_ISSUE
        condition: "{{ context.support_category == 'technical' }}"
      - signal_name: GENERAL_INQUIRY
        condition: "{{ context.support_category not in ['billing', 'technical'] }}"

  # Terminal nodes: handle the final outcomes
  NewOrderHandler:
    node_type: router
    event_triggers: [NEW_ORDER]
    event_emissions:
      - signal_name: ORDER_FLOW_COMPLETE

  CancelOrderHandler:
    node_type: router
    event_triggers: [CANCEL_ORDER]
    event_emissions:
      - signal_name: ORDER_FLOW_COMPLETE

  TrackOrderHandler:
    node_type: router
    event_triggers: [TRACK_ORDER]
    event_emissions:
      - signal_name: ORDER_FLOW_COMPLETE

  BillingHandler:
    node_type: router
    event_triggers: [BILLING_ISSUE]
    event_emissions:
      - signal_name: SUPPORT_FLOW_COMPLETE

  TechnicalHandler:
    node_type: router
    event_triggers: [TECHNICAL_ISSUE]
    event_emissions:
      - signal_name: SUPPORT_FLOW_COMPLETE

  GeneralHandler:
    node_type: router
    event_triggers: [GENERAL_INQUIRY]
    event_emissions:
      - signal_name: SUPPORT_FLOW_COMPLETE

  UnknownHandler:
    node_type: router
    event_triggers: [HANDLE_UNKNOWN]
    event_emissions:
      - signal_name: UNKNOWN_FLOW_COMPLETE
"""

# Simpler decision tree for documentation clarity
router_simple_decision_tree = """
example_workflow:
  # Level 1: Is the user premium or free?
  UserTierCheck:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PREMIUM_PATH
        condition: "{{ context.user_tier == 'premium' }}"
      - signal_name: FREE_PATH
        condition: "{{ context.user_tier == 'free' }}"

  # Level 2a: Premium users get feature checks
  PremiumFeatureRouter:
    node_type: router
    event_triggers: [PREMIUM_PATH]
    event_emissions:
      - signal_name: ENABLE_ADVANCED
        condition: "{{ context.feature_level == 'advanced' }}"
      - signal_name: ENABLE_BASIC
        condition: "{{ context.feature_level != 'advanced' }}"

  # Level 2b: Free users get upgrade prompts
  FreeUserRouter:
    node_type: router
    event_triggers: [FREE_PATH]
    event_emissions:
      - signal_name: SHOW_UPGRADE
        condition: "{{ context.show_upsell }}"
      - signal_name: CONTINUE_FREE
        condition: "{{ not context.show_upsell }}"
"""
