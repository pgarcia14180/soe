"""
Workflow definitions for Agent Nodes

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Agent is a convenience node that wraps the ReAct pattern:
Router -> Parameter Generation -> Tool Execution -> Response loop.

Note: You can build this pattern yourself using Tool + LLM + Router primitives.
See guide_patterns.py for a custom ReAct implementation.
"""

# Simple Agent with one tool
agent_simple = """
example_workflow:
  CalculatorAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "You are a calculator. Solve the user's math problem: {{ context.problem }}"
    tools: [calculator]
    output_field: result
    event_emissions:
      - signal_name: CALCULATION_DONE
"""

# Agent with conversation history (Identity)
agent_conversation = """
example_workflow:
  ChatAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "You are a helpful assistant. User says: {{ context.message }}"
    identity: user_session_123
    output_field: response
    event_emissions:
      - signal_name: RESPONSE_READY
"""

# Agent with multiple tools
agent_complex = """
example_workflow:
  ResearchAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Research the topic: {{ context.topic }}"
    tools: [search_web, summarize_text]
    output_field: report
    event_emissions:
      - signal_name: REPORT_READY
"""

# Agent with signal selection (LLM chooses which signal to emit)
agent_signal_selection = """
example_workflow:
  AnalysisAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Analyze the data and determine if it needs human review: {{ context.data }}"
    tools: [analyze_data]
    output_field: analysis
    event_emissions:
      - signal_name: AUTO_APPROVE
        condition: "The analysis shows the data is clearly valid"
      - signal_name: NEEDS_REVIEW
        condition: "The analysis shows the data requires human review"
      - signal_name: REJECT
        condition: "The analysis shows the data is clearly invalid"
"""
