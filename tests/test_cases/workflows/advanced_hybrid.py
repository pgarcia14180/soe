"""
Workflow definitions for Advanced Patterns: Hybrid Intelligence

These workflows demonstrate:
1. Mixing deterministic routers with LLM nodes
2. Safety rails around AI outputs
3. The "Centaur" pattern (code + AI)

Used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)
"""

# =============================================================================
# HYBRID PATTERN: Deterministic validation around LLM
# =============================================================================

# Safety rails: validate input → LLM generates → validate output
hybrid_safety_rails = """
safety_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INPUT_VALID
        condition: "{{ context.amount is defined and context.amount > 0 }}"
      - signal_name: INPUT_INVALID
        condition: "{{ context.amount is not defined or context.amount <= 0 }}"

  GenerateResponse:
    node_type: llm
    event_triggers: [INPUT_VALID]
    prompt: |
      Generate a professional message about a transaction of ${{ context.amount }}.
      Keep it brief and professional.
    output_field: generated_message
    event_emissions:
      - signal_name: MESSAGE_GENERATED

  ValidateOutput:
    node_type: router
    event_triggers: [MESSAGE_GENERATED]
    event_emissions:
      - signal_name: OUTPUT_SAFE
        condition: "{{ context.generated_message is defined and context.generated_message | length < 500 }}"
      - signal_name: OUTPUT_UNSAFE
        condition: "{{ context.generated_message is not defined or context.generated_message | length >= 500 }}"

  HandleInputError:
    node_type: router
    event_triggers: [INPUT_INVALID]
    event_emissions:
      - signal_name: ERROR

  Complete:
    node_type: router
    event_triggers: [OUTPUT_SAFE]
    event_emissions:
      - signal_name: DONE

  HandleOutputError:
    node_type: router
    event_triggers: [OUTPUT_UNSAFE]
    event_emissions:
      - signal_name: ERROR
"""

# =============================================================================
# DETERMINISTIC HYBRID: For testing without LLM
# =============================================================================

# Same pattern but deterministic (for testing)
deterministic_hybrid = """
hybrid_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INPUT_VALID
        condition: "{{ context.user_input is defined and context.user_input | length > 0 }}"
      - signal_name: INPUT_INVALID
        condition: "{{ context.user_input is not defined or context.user_input | length == 0 }}"

  ProcessInput:
    node_type: tool
    event_triggers: [INPUT_VALID]
    tool_name: process_input
    context_parameter_field: process_params
    output_field: processed_result
    event_emissions:
      - signal_name: PROCESSED

  ValidateOutput:
    node_type: router
    event_triggers: [PROCESSED]
    event_emissions:
      - signal_name: OUTPUT_VALID
        condition: "{{ context.processed_result is defined and context.processed_result.valid == true }}"
      - signal_name: OUTPUT_INVALID
        condition: "{{ context.processed_result is not defined or context.processed_result.valid != true }}"

  Complete:
    node_type: router
    event_triggers: [OUTPUT_VALID]
    event_emissions:
      - signal_name: DONE

  HandleError:
    node_type: router
    event_triggers: [INPUT_INVALID, OUTPUT_INVALID, PROCESS_FAILED]
    event_emissions:
      - signal_name: ERROR
"""

# =============================================================================
# RETRY PATTERN: LLM with deterministic retry logic
# =============================================================================

retry_pattern = """
retry_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ATTEMPT

  Generate:
    node_type: llm
    event_triggers: [ATTEMPT]
    prompt: "Generate a valid JSON object with fields: name, age"
    output_field: llm_output
    event_emissions:
      - signal_name: GENERATED

  Validate:
    node_type: router
    event_triggers: [GENERATED]
    event_emissions:
      - signal_name: VALID_JSON
        condition: "{{ context.llm_output is mapping }}"
      - signal_name: INVALID_JSON
        condition: "{{ context.llm_output is not mapping }}"

  IncrementRetry:
    node_type: router
    event_triggers: [INVALID_JSON]
    event_emissions:
      - signal_name: ATTEMPT
        condition: "{{ context.retry_count | default(0) < 3 }}"
      - signal_name: MAX_RETRIES
        condition: "{{ context.retry_count | default(0) >= 3 }}"

  Complete:
    node_type: router
    event_triggers: [VALID_JSON]
    event_emissions:
      - signal_name: DONE
"""
