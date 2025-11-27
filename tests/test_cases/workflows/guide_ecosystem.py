"""
Workflow definitions for Chapter 09: Workflows Ecosystem

These workflows demonstrate the ecosystem concepts:
- Multiple workflows in a registry
- Parallel workflow execution
- Workflow versioning through data persistence
- Fire-and-forget vs callback patterns
"""

# Multi-Workflow Registry: Multiple workflows work together
# This shows how you can have multiple workflows in the same registry
multi_workflow_registry = """
# Workflow 1: Entry point that delegates to specialized workflows
main_workflow:
  Classifier:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: HANDLE_TEXT
        condition: "{{ context.input_type == 'text' }}"
      - signal_name: HANDLE_IMAGE
        condition: "{{ context.input_type == 'image' }}"

  DelegateToTextProcessor:
    node_type: child
    event_triggers: [HANDLE_TEXT]
    child_workflow_name: text_processing_workflow
    child_initial_signals: [START]
    input_fields: [content]
    signals_to_parent: [TEXT_DONE]
    context_updates_to_parent: [text_result]
    event_emissions:
      - signal_name: PROCESSING_COMPLETE

  DelegateToImageProcessor:
    node_type: child
    event_triggers: [HANDLE_IMAGE]
    child_workflow_name: image_processing_workflow
    child_initial_signals: [START]
    input_fields: [content]
    signals_to_parent: [IMAGE_DONE]
    context_updates_to_parent: [image_result]
    event_emissions:
      - signal_name: PROCESSING_COMPLETE

  Finalize:
    node_type: router
    event_triggers: [PROCESSING_COMPLETE]
    event_emissions:
      - signal_name: COMPLETE

# Workflow 2: Specialized text processing
text_processing_workflow:
  AnalyzeText:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this text: {{ context.content }}"
    output_field: text_result
    event_emissions:
      - signal_name: TEXT_DONE

# Workflow 3: Specialized image processing
image_processing_workflow:
  AnalyzeImage:
    node_type: llm
    event_triggers: [START]
    prompt: "Describe this image: {{ context.content }}"
    output_field: image_result
    event_emissions:
      - signal_name: IMAGE_DONE
"""

# Fire-and-Forget Pattern: Start a workflow without waiting
fire_and_forget = """
main_workflow:
  LaunchBackground:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: TASK_LAUNCHED
      - signal_name: START_BACKGROUND

  StartBackgroundTask:
    node_type: child
    event_triggers: [START_BACKGROUND]
    child_workflow_name: background_workflow
    child_initial_signals: [START]
    input_fields: [task_data]
    # No signals_to_parent - we don't wait for completion

  ContinueImmediately:
    node_type: router
    event_triggers: [TASK_LAUNCHED]
    event_emissions:
      - signal_name: PARENT_COMPLETE

background_workflow:
  LongRunningTask:
    node_type: tool
    event_triggers: [START]
    tool_name: long_task
    context_parameter_field: task_data
    output_field: result
    event_emissions:
      - signal_name: BACKGROUND_DONE
"""

# Parallel Workflows: Multiple children running simultaneously
parallel_workflows = """
orchestrator_workflow:
  FanOut:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: START_WORKER_A
      - signal_name: START_WORKER_B
      - signal_name: START_WORKER_C

  WorkerA:
    node_type: child
    event_triggers: [START_WORKER_A]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    input_fields: [data_chunk_a]
    signals_to_parent: [WORKER_DONE]
    context_updates_to_parent: [result_a]
    event_emissions:
      - signal_name: A_COMPLETE

  WorkerB:
    node_type: child
    event_triggers: [START_WORKER_B]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    input_fields: [data_chunk_b]
    signals_to_parent: [WORKER_DONE]
    context_updates_to_parent: [result_b]
    event_emissions:
      - signal_name: B_COMPLETE

  WorkerC:
    node_type: child
    event_triggers: [START_WORKER_C]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    input_fields: [data_chunk_c]
    signals_to_parent: [WORKER_DONE]
    context_updates_to_parent: [result_c]
    event_emissions:
      - signal_name: C_COMPLETE

  Aggregate:
    node_type: router
    event_triggers: [A_COMPLETE, B_COMPLETE, C_COMPLETE]
    event_emissions:
      - signal_name: ALL_DONE
        condition: "{{ context.result_a and context.result_b and context.result_c }}"

worker_workflow:
  ProcessData:
    node_type: tool
    event_triggers: [START]
    tool_name: process_chunk
    context_parameter_field: data
    output_field: result
    event_emissions:
      - signal_name: WORKER_DONE
"""

# Workflow with External Trigger Capability
# This demonstrates how an external system can send signals to an existing execution
external_trigger = """
waiting_workflow:
  Initialize:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: WAITING_FOR_APPROVAL

  # This workflow pauses here. An external system must send APPROVED or REJECTED
  # using broadcast_signals with the execution_id

  HandleApproval:
    node_type: router
    event_triggers: [APPROVED]
    event_emissions:
      - signal_name: PROCESS_APPROVED

  HandleRejection:
    node_type: router
    event_triggers: [REJECTED]
    event_emissions:
      - signal_name: PROCESS_REJECTED

  ProcessApproved:
    node_type: tool
    event_triggers: [PROCESS_APPROVED]
    tool_name: finalize_approved
    output_field: final_result
    event_emissions:
      - signal_name: COMPLETE

  NotifyRejection:
    node_type: tool
    event_triggers: [PROCESS_REJECTED]
    tool_name: notify_rejection
    output_field: rejection_notice
    event_emissions:
      - signal_name: COMPLETE
"""

# Versioning Pattern: Context-based workflow routing
# Different versions can coexist by routing based on context
version_routing = """
entry_workflow:
  RouteByVersion:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: USE_V1
        condition: "{{ context.api_version == 'v1' }}"
      - signal_name: USE_V2
        condition: "{{ context.api_version == 'v2' }}"
      - signal_name: USE_LATEST
        condition: "{{ context.api_version is not defined }}"

  ExecuteV1:
    node_type: child
    event_triggers: [USE_V1]
    child_workflow_name: processor_v1
    child_initial_signals: [START]
    input_fields: [request]
    signals_to_parent: [V1_DONE]
    context_updates_to_parent: [response]

  ExecuteV2:
    node_type: child
    event_triggers: [USE_V2, USE_LATEST]
    child_workflow_name: processor_v2
    child_initial_signals: [START]
    input_fields: [request]
    signals_to_parent: [V2_DONE]
    context_updates_to_parent: [response]

  HandleV1Done:
    node_type: router
    event_triggers: [V1_DONE]
    event_emissions:
      - signal_name: COMPLETE

  HandleV2Done:
    node_type: router
    event_triggers: [V2_DONE]
    event_emissions:
      - signal_name: COMPLETE

processor_v1:
  ProcessOldWay:
    node_type: llm
    event_triggers: [START]
    prompt: "Process (v1 legacy format): {{ context.request }}"
    output_field: response
    event_emissions:
      - signal_name: V1_DONE

processor_v2:
  ProcessNewWay:
    node_type: llm
    event_triggers: [START]
    prompt: "Process with enhanced capabilities: {{ context.request }}"
    output_field: response
    event_emissions:
      - signal_name: V2_DONE
"""


# ============================================================================
# COMBINED CONFIG EXAMPLES (workflows + context_schema + identities)
# ============================================================================
# These demonstrate the recommended pattern where all configuration
# is in a single config object.

# Full ecosystem with schema validation and identity management
combined_ecosystem_config = """
workflows:
  main_workflow:
    Classifier:
      node_type: router
      event_triggers: [START]
      event_emissions:
        - signal_name: HANDLE_TEXT
          condition: "{{ context.input_type == 'text' }}"
        - signal_name: HANDLE_IMAGE
          condition: "{{ context.input_type == 'image' }}"

    DelegateToTextProcessor:
      node_type: child
      event_triggers: [HANDLE_TEXT]
      child_workflow_name: text_workflow
      child_initial_signals: [START]
      input_fields: [content]
      signals_to_parent: [DONE]
      context_updates_to_parent: [result]
      event_emissions:
        - signal_name: PROCESSING_COMPLETE

    DelegateToImageProcessor:
      node_type: child
      event_triggers: [HANDLE_IMAGE]
      child_workflow_name: image_workflow
      child_initial_signals: [START]
      input_fields: [content]
      signals_to_parent: [DONE]
      context_updates_to_parent: [result]
      event_emissions:
        - signal_name: PROCESSING_COMPLETE

    Finalize:
      node_type: router
      event_triggers: [PROCESSING_COMPLETE]
      event_emissions:
        - signal_name: COMPLETE

  text_workflow:
    AnalyzeText:
      node_type: llm
      event_triggers: [START]
      identity: text_analyzer
      prompt: "Analyze this text: {{ context.content }}"
      output_field: result
      event_emissions:
        - signal_name: DONE

  image_workflow:
    AnalyzeImage:
      node_type: llm
      event_triggers: [START]
      identity: image_analyzer
      prompt: "Describe this image: {{ context.content }}"
      output_field: result
      event_emissions:
        - signal_name: DONE

context_schema:
  content:
    type: string
    description: The input content to process
  result:
    type: object
    description: The processing result

identities:
  text_analyzer: "You are an expert text analyst. Provide detailed, structured analysis."
  image_analyzer: "You are an expert image analyst. Describe visual elements precisely."
"""

# Parallel workers with schema validation
combined_parallel_config = """
workflows:
  orchestrator_workflow:
    FanOut:
      node_type: router
      event_triggers: [START]
      event_emissions:
        - signal_name: START_WORKER_A
        - signal_name: START_WORKER_B
        - signal_name: START_WORKER_C

    WorkerA:
      node_type: child
      event_triggers: [START_WORKER_A]
      child_workflow_name: worker_workflow
      child_initial_signals: [START]
      input_fields: [chunk_a]
      signals_to_parent: [WORKER_DONE]
      context_updates_to_parent: [result_a]
      event_emissions:
        - signal_name: A_COMPLETE

    WorkerB:
      node_type: child
      event_triggers: [START_WORKER_B]
      child_workflow_name: worker_workflow
      child_initial_signals: [START]
      input_fields: [chunk_b]
      signals_to_parent: [WORKER_DONE]
      context_updates_to_parent: [result_b]
      event_emissions:
        - signal_name: B_COMPLETE

    WorkerC:
      node_type: child
      event_triggers: [START_WORKER_C]
      child_workflow_name: worker_workflow
      child_initial_signals: [START]
      input_fields: [chunk_c]
      signals_to_parent: [WORKER_DONE]
      context_updates_to_parent: [result_c]
      event_emissions:
        - signal_name: C_COMPLETE

    Aggregate:
      node_type: llm
      event_triggers: [A_COMPLETE, B_COMPLETE, C_COMPLETE]
      identity: aggregator
      prompt: |
        Aggregate the results:
        - Result A: {{ context.result_a }}
        - Result B: {{ context.result_b }}
        - Result C: {{ context.result_c }}
      output_field: final_result
      event_emissions:
        - signal_name: ALL_DONE

  worker_workflow:
    ProcessData:
      node_type: llm
      event_triggers: [START]
      identity: data_processor
      prompt: "Process this data chunk: {{ context.data }}"
      output_field: result
      event_emissions:
        - signal_name: WORKER_DONE

context_schema:
  chunk_a:
    type: object
    description: Data chunk for worker A
  chunk_b:
    type: object
    description: Data chunk for worker B
  chunk_c:
    type: object
    description: Data chunk for worker C
  result_a:
    type: object
    description: Processing result from worker A
  result_b:
    type: object
    description: Processing result from worker B
  result_c:
    type: object
    description: Processing result from worker C
  final_result:
    type: object
    description: Aggregated final result

identities:
  data_processor: "You are a data processing specialist. Extract and transform data accurately."
  aggregator: "You are an expert at synthesizing multiple data sources into coherent summaries."
"""

# Simple combined config for quick start
combined_simple_config = """
workflows:
  example_workflow:
    Analyze:
      node_type: llm
      event_triggers: [START]
      identity: analyst
      prompt: "Analyze: {{ context.input }}"
      output_field: analysis
      event_emissions:
        - signal_name: ANALYZED

    Summarize:
      node_type: llm
      event_triggers: [ANALYZED]
      identity: analyst
      prompt: "Summarize the analysis: {{ context.analysis }}"
      output_field: summary
      event_emissions:
        - signal_name: DONE

context_schema:
  input:
    type: string
    description: The input to analyze
  analysis:
    type: object
    description: Detailed analysis result
  summary:
    type: string
    description: A concise summary

identities:
  analyst: "You are a thorough analyst. Be precise and structured in your analysis."
"""
