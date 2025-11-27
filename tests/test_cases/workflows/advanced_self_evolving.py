"""
Workflow definitions for Advanced Patterns: Self-Evolving Workflows

These workflows demonstrate:
1. Injecting new workflows at runtime
2. Injecting nodes into existing workflows
3. LLM-driven workflow generation

Used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)
"""

# =============================================================================
# DETERMINISTIC WORKFLOW INJECTION
# =============================================================================

# Base workflow that will have a new workflow injected
soe_inject_workflow_base = """
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: soe_inject_workflow

  InjectNewWorkflow:
    node_type: tool
    event_triggers: [soe_inject_workflow]
    tool_name: soe_inject_workflow
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: WORKFLOW_INJECTED

  Complete:
    node_type: router
    event_triggers: [WORKFLOW_INJECTED]
    event_emissions:
      - signal_name: DONE
"""

# The workflow data to be injected (as a string in context)
injected_workflow_data = """
InjectedWorkflow:
  ProcessData:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INJECTED_COMPLETE
"""

# =============================================================================
# DETERMINISTIC NODE INJECTION
# =============================================================================

# Base workflow that will have a node injected
inject_node_base = """
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INJECT_NODE

  InjectNewNode:
    node_type: tool
    event_triggers: [INJECT_NODE]
    tool_name: soe_inject_node
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: NODE_INJECTED

  Complete:
    node_type: router
    event_triggers: [NODE_INJECTED]
    event_emissions:
      - signal_name: DONE
"""

# The node configuration to be injected (as a string in context)
injected_node_data = """
node_type: router
event_triggers: [TRIGGER_NEW_NODE]
event_emissions:
  - signal_name: NEW_NODE_COMPLETE
"""

# =============================================================================
# LLM-DRIVEN WORKFLOW GENERATION
# =============================================================================

# Workflow where an LLM generates a new workflow
# Uses schema extraction to output the exact parameters the tool needs
llm_workflow_generator = """
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GENERATE_WORKFLOW

  GenerateWorkflow:
    node_type: llm
    event_triggers: [GENERATE_WORKFLOW]
    prompt: |
      You are a workflow architect. Generate a simple SOE workflow.

      The workflow should be named "{{ context.workflow_name }}" and have:
      - A router node that triggers on START
      - Emit signal: GENERATED_COMPLETE

      Provide the workflow_name and the workflow_data (as YAML string).
    schema_name: Generated_WorkflowResponse
    output_field: inject_params
    event_emissions:
      - signal_name: WORKFLOW_GENERATED

  InjectGeneratedWorkflow:
    node_type: tool
    event_triggers: [WORKFLOW_GENERATED]
    tool_name: soe_inject_workflow
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: INJECTION_COMPLETE

  Complete:
    node_type: router
    event_triggers: [INJECTION_COMPLETE]
    event_emissions:
      - signal_name: DONE
"""

# =============================================================================
# LLM-DRIVEN NODE GENERATION
# =============================================================================

# Workflow where an LLM generates a node configuration
# Uses schema extraction to output the exact parameters the tool needs
llm_node_generator = """
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GENERATE_NODE

  GenerateNode:
    node_type: llm
    event_triggers: [GENERATE_NODE]
    prompt: |
      You are a workflow architect. Generate a SOE node configuration.

      The node should:
      - Be a router node
      - Trigger on signal: {{ context.trigger_signal }}
      - Emit signal: DYNAMIC_NODE_DONE

      Target workflow: {{ context.target_workflow }}
      Node name: {{ context.node_name }}

      Provide the workflow_name, node_name, and node_config_data (as YAML string).
    schema_name: Generated_NodeResponse
    output_field: inject_params
    event_emissions:
      - signal_name: NODE_GENERATED

  InjectGeneratedNode:
    node_type: tool
    event_triggers: [NODE_GENERATED]
    tool_name: soe_inject_node
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: NODE_INJECTION_COMPLETE

  Complete:
    node_type: router
    event_triggers: [NODE_INJECTION_COMPLETE]
    event_emissions:
      - signal_name: DONE
"""
