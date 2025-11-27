"""
Workflow definitions for Tool Nodes

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Tool is one of the three core node types in SOE. It executes a function directly
without LLM involvement. Parameters come from context, output goes to context.
"""

# Simple Tool Node - execute a function
tool_simple = """
example_workflow:
  SendEmail:
    node_type: tool
    event_triggers: [START]
    tool_name: send_email
    context_parameter_field: email_data
    output_field: email_result
    event_emissions:
      - signal_name: EMAIL_SENT
"""

# Tool Node with conditional routing
tool_with_routing = """
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS

  SendReceipt:
    node_type: tool
    event_triggers: [PAYMENT_SUCCESS]
    tool_name: send_receipt
    context_parameter_field: payment_result
    output_field: receipt_sent
    event_emissions:
      - signal_name: RECEIPT_SENT
"""

# Tool chain - multiple tools in sequence
tool_chain = """
example_workflow:
  FetchData:
    node_type: tool
    event_triggers: [START]
    tool_name: fetch_data
    context_parameter_field: query
    output_field: raw_data
    event_emissions:
      - signal_name: DATA_FETCHED

  TransformData:
    node_type: tool
    event_triggers: [DATA_FETCHED]
    tool_name: transform_data
    context_parameter_field: raw_data
    output_field: transformed_data
    event_emissions:
      - signal_name: DATA_TRANSFORMED
"""

# Tool with conditional event emissions
tool_conditional_emissions = """
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS
        condition: "{{ result.status == 'approved' }}"
      - signal_name: PAYMENT_DECLINED
        condition: "{{ result.status == 'declined' }}"
      - signal_name: PAYMENT_PENDING
        condition: "{{ result.status == 'pending' }}"
"""

# Tool with conditions using both result and context
tool_result_and_context_conditions = """
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS
        condition: "{{ result.status == 'approved' }}"
      - signal_name: VIP_PAYMENT_SUCCESS
        condition: "{{ result.status == 'approved' and context.customer.is_vip }}"
      - signal_name: LARGE_PAYMENT_SUCCESS
        condition: "{{ result.status == 'approved' and context.payment_data.amount > 1000 }}"
"""
