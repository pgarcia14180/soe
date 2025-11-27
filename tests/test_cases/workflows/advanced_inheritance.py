"""
Workflow definitions for Configuration and Context Inheritance.

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Inheritance enables workflow chaining and context sharing across executions.
"""

# Basic config inheritance - inherit workflows, identity, schema from existing execution
INHERIT_CONFIG_BASIC = """
workflows:
  main_workflow:
    ProcessData:
      node_type: tool
      event_triggers: [START]
      tool_name: process
      context_parameter_field: input_data
      output_field: result
      event_emissions:
        - signal_name: PROCESSED

    Complete:
      node_type: router
      event_triggers: [PROCESSED]
      event_emissions:
        - signal_name: COMPLETE

identities:
  assistant: "You are a helpful assistant."
  analyst: "You are a data analyst."

context_schema:
  input_data:
    type: object
    description: "Input data to process"
  result:
    type: object
    description: "Processing result"
"""

# Continuation workflow - uses inherited config to run a different workflow
CONTINUATION_WORKFLOW = """
workflows:
  main_workflow:
    ProcessData:
      node_type: tool
      event_triggers: [START]
      tool_name: process
      context_parameter_field: input_data
      output_field: result
      event_emissions:
        - signal_name: PROCESSED

    Complete:
      node_type: router
      event_triggers: [PROCESSED]
      event_emissions:
        - signal_name: COMPLETE

  continuation_workflow:
    ContinueWork:
      node_type: tool
      event_triggers: [START]
      tool_name: continue_process
      context_parameter_field: result
      output_field: final_result
      event_emissions:
        - signal_name: CONTINUED

    Finalize:
      node_type: router
      event_triggers: [CONTINUED]
      event_emissions:
        - signal_name: FINALIZED

identities:
  assistant: "You are a helpful assistant."

context_schema:
  input_data:
    type: object
  result:
    type: object
  final_result:
    type: object
"""

# Context inheritance with operational reset
CONTEXT_INHERITANCE_EXAMPLE = """
workflows:
  main_workflow:
    Step1:
      node_type: tool
      event_triggers: [START]
      tool_name: step1_tool
      output_field: step1_result
      event_emissions:
        - signal_name: STEP1_DONE

    Step2:
      node_type: tool
      event_triggers: [STEP1_DONE]
      tool_name: step2_tool
      context_parameter_field: step1_result
      output_field: step2_result
      event_emissions:
        - signal_name: COMPLETE

  retry_workflow:
    RetryStep2:
      node_type: tool
      event_triggers: [START]
      tool_name: step2_tool_v2
      context_parameter_field: step1_result
      output_field: step2_result
      event_emissions:
        - signal_name: RETRY_COMPLETE
"""

# LLM workflow with identity inheritance
LLM_IDENTITY_INHERITANCE = """
workflows:
  conversation_workflow:
    FirstMessage:
      node_type: llm
      event_triggers: [START]
      identity: assistant
      prompt: "User says: {{ context.user_message }}"
      output_field: assistant_response
      event_emissions:
        - signal_name: RESPONDED

    Complete:
      node_type: router
      event_triggers: [RESPONDED]
      event_emissions:
        - signal_name: CONVERSATION_DONE

  followup_workflow:
    FollowUp:
      node_type: llm
      event_triggers: [START]
      identity: assistant
      prompt: "User follows up: {{ context.followup_message }}"
      output_field: followup_response
      event_emissions:
        - signal_name: FOLLOWUP_DONE

identities:
  assistant: "You are a helpful assistant. Be concise and friendly."
"""

# Multi-phase workflow demonstrating config + context inheritance together
MULTI_PHASE_WORKFLOW = """
workflows:
  phase1_workflow:
    Analyze:
      node_type: llm
      event_triggers: [START]
      identity: analyst
      prompt: "Analyze this data: {{ context.raw_data }}"
      output_field: analysis
      event_emissions:
        - signal_name: ANALYSIS_DONE

    Validate:
      node_type: tool
      event_triggers: [ANALYSIS_DONE]
      tool_name: validate_analysis
      context_parameter_field: analysis
      output_field: validated_analysis
      event_emissions:
        - signal_name: PHASE1_COMPLETE

  phase2_workflow:
    Generate:
      node_type: llm
      event_triggers: [START]
      identity: writer
      prompt: "Based on analysis: {{ context.validated_analysis }}, generate report"
      output_field: report
      event_emissions:
        - signal_name: REPORT_DONE

    Finalize:
      node_type: router
      event_triggers: [REPORT_DONE]
      event_emissions:
        - signal_name: PHASE2_COMPLETE

identities:
  analyst: "You are a data analyst. Focus on insights and patterns."
  writer: "You are a technical writer. Be clear and professional."

context_schema:
  raw_data:
    type: string
    description: "Raw data to analyze"
  analysis:
    type: object
    description: "Analysis results"
  validated_analysis:
    type: object
    description: "Validated analysis"
  report:
    type: string
    description: "Generated report"
"""
