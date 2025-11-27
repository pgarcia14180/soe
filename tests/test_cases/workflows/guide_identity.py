"""
Workflow definitions for Identity and Conversation History

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Identity enables conversation history persistence across LLM calls.
LLM nodes with the same identity share conversation history.

KEY CONCEPT: Identity only matters when you have MULTIPLE LLM calls.
The conversation history from previous calls with the same identity
is included in subsequent prompts.
"""

# Multi-turn conversation - same identity across workflow
# The second LLM node will see the first node's conversation in history
MULTI_TURN_SAME_IDENTITY = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: conversation_abc
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: conversation_abc
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Multi-turn with DIFFERENT identities - history should NOT be shared
MULTI_TURN_DIFFERENT_IDENTITY = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: session_A
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: session_B
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Multi-turn with NO identity - history should be empty for both
MULTI_TURN_NO_IDENTITY = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Dynamic identity from context - same session_id means shared history
DYNAMIC_IDENTITY_MULTI_TURN = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: "{{ context.session_id }}"
    prompt: "Process first request: {{ context.request1 }}"
    output_field: firstResult
    event_emissions:
      - signal_name: FIRST_DONE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_DONE]
    identity: "{{ context.session_id }}"
    prompt: "Process second request: {{ context.request2 }}"
    output_field: secondResult
    event_emissions:
      - signal_name: SECOND_DONE
"""

# Three turns to show history accumulates
THREE_TURN_CONVERSATION = """
example_workflow:
  Turn1:
    node_type: llm
    event_triggers: [START]
    identity: long_conversation
    prompt: "User says: {{ context.msg1 }}"
    output_field: response1
    event_emissions:
      - signal_name: TURN1_DONE

  Turn2:
    node_type: llm
    event_triggers: [TURN1_DONE]
    identity: long_conversation
    prompt: "User says: {{ context.msg2 }}"
    output_field: response2
    event_emissions:
      - signal_name: TURN2_DONE

  Turn3:
    node_type: llm
    event_triggers: [TURN2_DONE]
    identity: long_conversation
    prompt: "User says: {{ context.msg3 }}"
    output_field: response3
    event_emissions:
      - signal_name: TURN3_DONE
"""


# Legacy exports for backward compatibility
IDENTITY_BASIC_EXAMPLE = MULTI_TURN_SAME_IDENTITY
IDENTITY_WITH_CONTEXT_EXAMPLE = DYNAMIC_IDENTITY_MULTI_TURN
MULTI_TURN_EXAMPLE = MULTI_TURN_SAME_IDENTITY
DYNAMIC_IDENTITY_EXAMPLE = DYNAMIC_IDENTITY_MULTI_TURN
NO_IDENTITY_EXAMPLE = MULTI_TURN_NO_IDENTITY


# ============================================================================
# EDGE CASE WORKFLOWS
# ============================================================================

# Empty identity string - treated as no identity
EMPTY_IDENTITY = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: ""
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: ""
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Identity with special characters
IDENTITY_SPECIAL_CHARS = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: "user@domain.com/session:123"
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: "user@domain.com/session:123"
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Dynamic identity that resolves to empty string
DYNAMIC_IDENTITY_EMPTY = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: "{{ context.missing_session_id }}"
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: "{{ context.missing_session_id }}"
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Identity switch mid-workflow
IDENTITY_SWITCH_MID_WORKFLOW = """
example_workflow:
  Turn1:
    node_type: llm
    event_triggers: [START]
    identity: session_alpha
    prompt: "User says: {{ context.msg1 }}"
    output_field: response1
    event_emissions:
      - signal_name: TURN1_DONE

  Turn2:
    node_type: llm
    event_triggers: [TURN1_DONE]
    identity: session_beta
    prompt: "User says: {{ context.msg2 }}"
    output_field: response2
    event_emissions:
      - signal_name: TURN2_DONE

  Turn3:
    node_type: llm
    event_triggers: [TURN2_DONE]
    identity: session_alpha
    prompt: "User says: {{ context.msg3 }}"
    output_field: response3
    event_emissions:
      - signal_name: TURN3_DONE
"""

# Parallel LLM calls with same identity - race condition test
PARALLEL_SAME_IDENTITY = """
example_workflow:
  SpawnBoth:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: TRIGGER_BOTH

  CallA:
    node_type: llm
    event_triggers: [TRIGGER_BOTH]
    identity: shared_session
    prompt: "Process request A: {{ context.requestA }}"
    output_field: responseA
    event_emissions:
      - signal_name: A_DONE

  CallB:
    node_type: llm
    event_triggers: [TRIGGER_BOTH]
    identity: shared_session
    prompt: "Process request B: {{ context.requestB }}"
    output_field: responseB
    event_emissions:
      - signal_name: B_DONE

  WaitForBoth:
    node_type: router
    event_triggers: [A_DONE, B_DONE]
    event_emissions:
      - signal_name: ALL_DONE
        condition: "{{ 'A_DONE' in context.__operational__.signals and 'B_DONE' in context.__operational__.signals }}"
"""

# Very long identity string
LONG_IDENTITY = """
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: "this_is_a_very_long_identity_string_that_might_exceed_normal_limits_user_12345_session_67890_timestamp_20241227_random_uuid_abc123def456"
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: "this_is_a_very_long_identity_string_that_might_exceed_normal_limits_user_12345_session_67890_timestamp_20241227_random_uuid_abc123def456"
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
"""

# Skill pattern - routing to different LLM identities
SKILL_PATTERN_EXAMPLE = """
example_workflow:
  SkillRouter:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CODING_SKILL
        condition: "{{ 'code' in context.request|lower }}"
      - signal_name: WRITING_SKILL
        condition: "{{ 'write' in context.request|lower }}"
      - signal_name: GENERAL_SKILL
        condition: "{{ 'code' not in context.request|lower and 'write' not in context.request|lower }}"

  CodingAssistant:
    node_type: llm
    event_triggers: [CODING_SKILL]
    identity: "{{ context.user_id }}_coding"
    prompt: "You are a coding assistant. Help with: {{ context.request }}"
    output_field: response
    event_emissions:
      - signal_name: SKILL_COMPLETE

  WritingAssistant:
    node_type: llm
    event_triggers: [WRITING_SKILL]
    identity: "{{ context.user_id }}_writing"
    prompt: "You are a writing assistant. Help with: {{ context.request }}"
    output_field: response
    event_emissions:
      - signal_name: SKILL_COMPLETE

  GeneralAssistant:
    node_type: llm
    event_triggers: [GENERAL_SKILL]
    identity: "{{ context.user_id }}_general"
    prompt: "Help with: {{ context.request }}"
    output_field: response
    event_emissions:
      - signal_name: SKILL_COMPLETE
"""


# ============================================================================
# COMBINED CONFIG EXAMPLES (workflows + identities in single config)
# ============================================================================
# These demonstrate the preferred pattern where identities are defined
# alongside workflows. Each identity maps to a system prompt.

COMBINED_IDENTITY_CONFIG = """
workflows:
  example_workflow:
    FirstTurn:
      node_type: llm
      event_triggers: [START]
      identity: helpful_assistant
      prompt: "Start a conversation about {{ context.topic }}"
      output_field: firstResponse
      event_emissions:
        - signal_name: FIRST_COMPLETE

    SecondTurn:
      node_type: llm
      event_triggers: [FIRST_COMPLETE]
      identity: helpful_assistant
      prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
      output_field: secondResponse
      event_emissions:
        - signal_name: CONVERSATION_COMPLETE

identities:
  helpful_assistant: "You are a friendly and knowledgeable assistant who explains topics clearly."
"""

COMBINED_MULTI_IDENTITY_CONFIG = """
workflows:
  example_workflow:
    SkillRouter:
      node_type: router
      event_triggers: [START]
      event_emissions:
        - signal_name: CODING_SKILL
          condition: "{{ 'code' in context.request|lower }}"
        - signal_name: WRITING_SKILL
          condition: "{{ 'write' in context.request|lower }}"

    CodingAssistant:
      node_type: llm
      event_triggers: [CODING_SKILL]
      identity: coding_expert
      prompt: "Help with: {{ context.request }}"
      output_field: response
      event_emissions:
        - signal_name: SKILL_COMPLETE

    WritingAssistant:
      node_type: llm
      event_triggers: [WRITING_SKILL]
      identity: writing_expert
      prompt: "Help with: {{ context.request }}"
      output_field: response
      event_emissions:
        - signal_name: SKILL_COMPLETE

identities:
  coding_expert: "You are an expert programmer. Provide clear, well-documented code examples."
  writing_expert: "You are a skilled writer. Focus on clarity, grammar, and style."
"""

# Combined config with BOTH context_schema AND identities
COMBINED_FULL_CONFIG = """
workflows:
  example_workflow:
    ExtractData:
      node_type: llm
      event_triggers: [START]
      identity: data_analyst
      prompt: "Extract key information from: {{ context.input }}"
      output_field: extracted_data
      event_emissions:
        - signal_name: DATA_EXTRACTED

    SummarizeData:
      node_type: llm
      event_triggers: [DATA_EXTRACTED]
      identity: data_analyst
      prompt: "Summarize the extracted data: {{ context.extracted_data }}"
      output_field: summary
      event_emissions:
        - signal_name: DONE

context_schema:
  extracted_data:
    type: object
    description: Structured data extracted from input
  summary:
    type: string
    description: A concise summary of the extracted data

identities:
  data_analyst: "You are a data analyst. Be precise, structured, and thorough in your analysis."
"""
