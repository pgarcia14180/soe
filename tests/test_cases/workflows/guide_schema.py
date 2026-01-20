"""
Workflow definitions for Schema Validation

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Schemas provide optional type validation for context fields.
They ensure LLM outputs match expected types (string, integer, object, list, boolean).
"""

# Schema with string output - basic validation
SCHEMA_STRING_EXAMPLE = """
example_workflow:
  SummarizeLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Summarize the following text in one sentence: {{ context.input_text }}"
    output_field: summary
    event_emissions:
      - signal_name: SUMMARY_COMPLETE
"""

SCHEMA_STRING_DEFINITION = {
    "example_workflow": {
        "summary": {
            "type": "string",
            "description": "A one-sentence summary of the input text"
        }
    }
}

# Schema with integer output - numeric validation
SCHEMA_INTEGER_EXAMPLE = """
example_workflow:
  CounterLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Count the number of words in this text: {{ context.input_text }}. Return only the count."
    output_field: word_count
    event_emissions:
      - signal_name: COUNT_COMPLETE
"""

SCHEMA_INTEGER_DEFINITION = {
    "example_workflow": {
        "word_count": {
            "type": "integer",
            "description": "The number of words in the input text"
        }
    }
}

# Schema with object output - structured data validation
SCHEMA_OBJECT_EXAMPLE = """
example_workflow:
  ExtractorLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Extract the person's name and age from: {{ context.input_text }}. Return as JSON with 'name' and 'age' fields."
    output_field: person_data
    event_emissions:
      - signal_name: EXTRACTION_COMPLETE
"""

SCHEMA_OBJECT_DEFINITION = {
    "example_workflow": {
        "person_data": {
            "type": "object",
            "description": "Extracted person data with name and age"
        }
    }
}

# Schema with list output - array validation
SCHEMA_LIST_EXAMPLE = """
example_workflow:
  KeywordLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Extract the top 3 keywords from: {{ context.input_text }}. Return as a list of strings."
    output_field: keywords
    event_emissions:
      - signal_name: KEYWORDS_EXTRACTED
"""

SCHEMA_LIST_DEFINITION = {
    "example_workflow": {
        "keywords": {
            "type": "list",
            "description": "List of extracted keywords"
        }
    }
}

# Schema with boolean output - true/false validation
SCHEMA_BOOLEAN_EXAMPLE = """
example_workflow:
  SentimentLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Is this text positive? {{ context.input_text }}. Answer with true or false."
    output_field: is_positive
    event_emissions:
      - signal_name: SENTIMENT_CHECKED
"""

SCHEMA_BOOLEAN_DEFINITION = {
    "example_workflow": {
        "is_positive": {
            "type": "boolean",
            "description": "Whether the text has positive sentiment"
        }
    }
}

# Schema with multiple fields - complex workflow
SCHEMA_MULTI_FIELD_EXAMPLE = """
example_workflow:
  AnalyzerLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this text: {{ context.input_text }}. Extract the topic and key points."
    output_field: topic
    event_emissions:
      - signal_name: TOPIC_EXTRACTED

  SummarizerLLM:
    node_type: llm
    event_triggers: [TOPIC_EXTRACTED]
    prompt: "Given the topic '{{ context.topic }}', provide a brief summary of: {{ context.input_text }}"
    output_field: summary
    event_emissions:
      - signal_name: ANALYSIS_COMPLETE
"""

SCHEMA_MULTI_FIELD_DEFINITION = {
    "example_workflow": {
        "topic": {
            "type": "string",
            "description": "The main topic of the text"
        },
        "summary": {
            "type": "string",
            "description": "A brief summary based on the topic"
        }
    }
}

# Schema with tool integration - LLM output feeds into tool
SCHEMA_TOOL_INTEGRATION_EXAMPLE = """
example_workflow:
  ParameterExtractor:
    node_type: llm
    event_triggers: [START]
    prompt: "Extract the operation and numbers from: {{ context.user_request }}. Return JSON with 'operation' (add/multiply) and 'numbers' (list of integers)."
    output_field: params
    event_emissions:
      - signal_name: PARAMS_EXTRACTED

  Calculator:
    node_type: tool
    event_triggers: [PARAMS_EXTRACTED]
    tool_name: calculate
    context_parameter_field: params
    output_field: result
    event_emissions:
      - signal_name: CALCULATED
"""

SCHEMA_TOOL_INTEGRATION_DEFINITION = {
    "example_workflow": {
        "params": {
            "type": "object",
            "description": "Extracted parameters with operation and numbers"
        },
        "result": {
            "type": "object",
            "description": "Calculation result"
        }
    }
}

# Agent with schema - output validation for agent final response
SCHEMA_AGENT_EXAMPLE = """
example_workflow:
  DataAgent:
    node_type: agent
    event_triggers: [START]
    system_prompt: "You are a helpful assistant that processes data requests."
    user_prompt: "Process this request: {{ context.user_request }}"
    output_field: response
    available_tools: [fetch_data]
    event_emissions:
      - signal_name: AGENT_COMPLETE
"""

SCHEMA_AGENT_DEFINITION = {
    "example_workflow": {
        "response": {
            "type": "string",
            "description": "The agent's final response to the user"
        }
    }
}

COMBINED_AGENT_SCHEMA_CONFIG = """
workflows:
  example_workflow:
    DataAgent:
      node_type: agent
      event_triggers: [START]
      prompt: "Process this request: {{ context.user_request }}"
      tools: [fetch_data]
      output_field: response
      event_emissions:
        - signal_name: AGENT_COMPLETE

context_schema:
  response:
    type: string
    description: The agent's final response to the user
"""

# No schema - demonstrates that schemas are optional
NO_SCHEMA_EXAMPLE = """
example_workflow:
  FreeLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Do whatever you want with: {{ context.input_text }}"
    output_field: output
    event_emissions:
      - signal_name: DONE
"""


# ============================================================================
# COMBINED CONFIG EXAMPLES (workflows + context_schema in single config)
# ============================================================================
# These demonstrate the preferred pattern where context_schema is defined
# alongside workflows. The schema is automatically saved keyed by execution_id.

COMBINED_STRING_SCHEMA_CONFIG = """
workflows:
  example_workflow:
    SummarizeLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Summarize the following text in one sentence: {{ context.input_text }}"
      output_field: summary
      event_emissions:
        - signal_name: SUMMARY_COMPLETE

context_schema:
  summary:
    type: string
    description: A one-sentence summary of the input text
"""

COMBINED_INTEGER_SCHEMA_CONFIG = """
workflows:
  example_workflow:
    CounterLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Count the number of words in this text: {{ context.input_text }}. Return only the count."
      output_field: word_count
      event_emissions:
        - signal_name: COUNT_COMPLETE

context_schema:
  word_count:
    type: integer
    description: The number of words in the input text
"""

COMBINED_OBJECT_SCHEMA_CONFIG = """
workflows:
  example_workflow:
    ExtractorLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Extract the person's name and age from: {{ context.input_text }}. Return as JSON with 'name' and 'age' fields."
      output_field: person_data
      event_emissions:
        - signal_name: EXTRACTION_COMPLETE

context_schema:
  person_data:
    type: object
    description: Extracted person data with name and age
    properties:
      name:
        type: string
      age:
        type: integer
"""

COMBINED_MULTI_FIELD_CONFIG = """
workflows:
  example_workflow:
    AnalyzerLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Analyze this text: {{ context.input_text }}. Extract the topic and key points."
      output_field: topic
      event_emissions:
        - signal_name: TOPIC_EXTRACTED

    SummarizerLLM:
      node_type: llm
      event_triggers: [TOPIC_EXTRACTED]
      prompt: "Given the topic '{{ context.topic }}', provide a brief summary of: {{ context.input_text }}"
      output_field: summary
      event_emissions:
        - signal_name: ANALYSIS_COMPLETE

context_schema:
  topic:
    type: string
    description: The main topic of the text
  summary:
    type: string
    description: A brief summary based on the topic
"""

COMBINED_TOOL_INTEGRATION_CONFIG = """
workflows:
  example_workflow:
    ParameterExtractor:
      node_type: llm
      event_triggers: [START]
      prompt: "Extract the operation and numbers from: {{ context.user_request }}. Return JSON with 'operation' (add/multiply) and 'numbers' (list of integers)."
      output_field: params
      event_emissions:
        - signal_name: PARAMS_EXTRACTED

    Calculator:
      node_type: tool
      event_triggers: [PARAMS_EXTRACTED]
      tool_name: calculate
      context_parameter_field: params
      output_field: result
      event_emissions:
        - signal_name: CALCULATED

context_schema:
  params:
    type: object
    description: Extracted parameters with operation and numbers
    properties:
      operation:
        type: string
      numbers:
        type: list
        items:
          type: integer
  result:
    type: object
    description: Calculation result
"""

COMBINED_LIST_SCHEMA_CONFIG = """
workflows:
  example_workflow:
    KeywordLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Extract the top 3 keywords from: {{ context.input_text }}. Return as a list of strings."
      output_field: keywords
      event_emissions:
        - signal_name: KEYWORDS_EXTRACTED

context_schema:
  keywords:
    type: list
    description: List of extracted keywords
    items:
      type: string
"""

COMBINED_BOOLEAN_SCHEMA_CONFIG = """
workflows:
  example_workflow:
    SentimentLLM:
      node_type: llm
      event_triggers: [START]
      prompt: "Is this text positive? {{ context.input_text }}. Answer with true or false."
      output_field: is_positive
      event_emissions:
        - signal_name: SENTIMENT_CHECKED

context_schema:
  is_positive:
    type: boolean
    description: Whether the text has positive sentiment
"""
