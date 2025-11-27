"""
Workflow definitions for LLM Nodes

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

LLM is one of the three core node types in SOE. It makes a single LLM call
(no tool calling, no loops) and stores the result in context.
"""

# Simple LLM node - direct call without agent loop
simple_llm_call = """
example_workflow:
  SimpleLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Summarize the following text in one sentence: {{ context.text }}"
    output_field: summary
    event_emissions:
      - signal_name: SUMMARY_COMPLETE
"""

# LLM node with conversation history (identity)
llm_with_identity = """
example_workflow:
  ChatAssistant:
    node_type: llm
    event_triggers: [START]
    prompt: "You are a helpful assistant. User says: {{ context.message }}"
    output_field: response
    identity: user_chat_session
    event_emissions:
      - signal_name: RESPONSE_COMPLETE
"""

# LLM chain - multiple LLM nodes in sequence
llm_chain = """
example_workflow:
  Translator:
    node_type: llm
    event_triggers: [START]
    prompt: "Translate the following to Spanish: {{ context.text }}"
    output_field: spanish_text
    event_emissions:
      - signal_name: TRANSLATED

  Summarizer:
    node_type: llm
    event_triggers: [TRANSLATED]
    prompt: "Summarize this Spanish text: {{ context.spanish_text }}"
    output_field: summary
    event_emissions:
      - signal_name: CHAIN_COMPLETE
"""

# LLM with signal selection (resolution step)
llm_signal_selection = """
example_workflow:
  SentimentAnalyzer:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze the sentiment of: {{ context.user_message }}"
    output_field: analysis
    event_emissions:
      - signal_name: POSITIVE
        condition: "The message expresses positive sentiment"
      - signal_name: NEGATIVE
        condition: "The message expresses negative sentiment"
      - signal_name: NEUTRAL
        condition: "The message is neutral or factual"
"""
