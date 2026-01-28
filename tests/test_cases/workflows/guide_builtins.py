"""
Workflow definitions for Built-in Tools

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Built-in tools are always available and enable self-evolution patterns.
They require no registration - SOE provides them automatically.
"""

# soe_explore_docs - Make SOE self-aware by exploring its own documentation
builtin_soe_explore_docs = """
example_workflow:
  ExploreDocs:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: docs_list
    event_emissions:
      - signal_name: DOCS_LISTED
"""

# soe_explore_docs with search
builtin_soe_explore_docs_search = """
example_workflow:
  SearchDocs:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: search_results
    event_emissions:
      - signal_name: SEARCH_COMPLETE
"""

# soe_explore_docs read section
builtin_soe_explore_docs_read = """
example_workflow:
  ReadGuide:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: guide_content
    event_emissions:
      - signal_name: GUIDE_READ
"""

# soe_get_workflows - Query registered workflow definitions
builtin_soe_get_workflows = """
example_workflow:
  GetWorkflows:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_workflows
    output_field: workflows_list
    event_emissions:
      - signal_name: WORKFLOWS_RETRIEVED
"""

# soe_inject_workflow - Add new workflows at runtime
builtin_soe_inject_workflow = """
example_workflow:
  InjectNew:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_workflow
    context_parameter_field: workflow_to_inject
    output_field: injection_result
    event_emissions:
      - signal_name: WORKFLOW_INJECTED
        condition: "{{ result.status == 'success' }}"
      - signal_name: INJECTION_FAILED
        condition: "{{ result.status != 'success' }}"
"""

# soe_inject_node - Add or modify nodes in existing workflows
builtin_inject_node = """
example_workflow:
  InjectNode:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_node
    context_parameter_field: node_to_inject
    output_field: node_injection_result
    event_emissions:
      - signal_name: NODE_INJECTED
        condition: "{{ result.status == 'success' }}"
"""

# soe_get_context - Read execution context
builtin_soe_get_context = """
example_workflow:
  GetContext:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_context
    output_field: current_context
    event_emissions:
      - signal_name: CONTEXT_RETRIEVED
"""

# soe_update_context - Modify execution context
builtin_soe_update_context = """
example_workflow:
  UpdateContext:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_update_context
    context_parameter_field: context_updates
    output_field: update_result
    event_emissions:
      - signal_name: CONTEXT_UPDATED
"""

# soe_copy_context - Clone context for parallel execution
builtin_soe_copy_context = """
example_workflow:
  CopyContext:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_copy_context
    context_parameter_field: copy_params
    output_field: copy_result
    event_emissions:
      - signal_name: CONTEXT_COPIED
"""

# Combined: Self-aware workflow that explores and evolves
builtin_self_aware = """
self_aware_workflow:
  ExploreCapabilities:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: capabilities_tree
    event_emissions:
      - signal_name: CAPABILITIES_KNOWN

  QueryCurrentState:
    node_type: tool
    event_triggers: [CAPABILITIES_KNOWN]
    tool_name: soe_get_workflows
    output_field: current_workflows
    event_emissions:
      - signal_name: STATE_KNOWN
"""

# soe_remove_workflow - Remove workflows from registry
builtin_soe_remove_workflow = """
example_workflow:
  RemoveOldWorkflow:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_remove_workflow
    context_parameter_field: remove_params
    output_field: removal_result
    event_emissions:
      - signal_name: WORKFLOW_REMOVED
"""

# soe_remove_node - Remove nodes from workflows
builtin_soe_remove_node = """
example_workflow:
  RemoveNode:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_remove_node
    context_parameter_field: remove_params
    output_field: node_removal_result
    event_emissions:
      - signal_name: NODE_REMOVED
"""

# soe_list_contexts - Discover available contexts
builtin_soe_list_contexts = """
example_workflow:
  ListAllContexts:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_list_contexts
    output_field: available_contexts
    event_emissions:
      - signal_name: CONTEXTS_LISTED
"""

# Evolution pattern - Complete self-evolution workflow
builtin_evolution_pattern = """
evolving_workflow:
  AnalyzeState:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_workflows
    output_field: current_state
    event_emissions:
      - signal_name: STATE_ANALYZED

  ApplyImprovement:
    node_type: tool
    event_triggers: [STATE_ANALYZED]
    tool_name: soe_inject_node
    context_parameter_field: designed_node
    output_field: injection_result
    event_emissions:
      - signal_name: EVOLVED
"""

# Metacognitive workflow - LLM explores docs and reasons about them
builtin_metacognitive = """
metacognitive_workflow:
  DiscoverCapabilities:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: soe_capabilities
    event_emissions:
      - signal_name: CAPABILITIES_DISCOVERED

  ReadRelevantGuide:
    node_type: tool
    event_triggers: [READ_GUIDE]
    tool_name: soe_explore_docs
    context_parameter_field: guide_params
    output_field: guide_content
    event_emissions:
      - signal_name: KNOWLEDGE_ACQUIRED
"""

# Reflective workflow - Get context and reflect on state
builtin_reflective = """
reflective_workflow:
  GatherState:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_context
    output_field: full_state
    event_emissions:
      - signal_name: STATE_GATHERED
"""

# soe_add_signal - Add signals to nodes at runtime
builtin_soe_add_signal = """
example_workflow:
  AddNewSignal:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_add_signal
    context_parameter_field: signal_params
    output_field: signal_result
    event_emissions:
      - signal_name: SIGNAL_ADDED
"""

# soe_list_contexts with file backend - Discover all available contexts
builtin_soe_list_contexts_detailed = """
example_workflow:
  DiscoverContexts:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_list_contexts
    output_field: all_contexts
    event_emissions:
      - signal_name: DISCOVERY_COMPLETE
"""

# soe_call_tool - Dynamically invoke any registered tool by name
builtin_soe_call_tool = """
example_workflow:
  CallDynamicTool:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_call_tool
    context_parameter_field: tool_invocation
    output_field: tool_result
    event_emissions:
      - signal_name: TOOL_CALLED
"""

# soe_get_available_tools - List all registered tools
builtin_soe_get_available_tools = """
example_workflow:
  ListTools:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_available_tools
    output_field: available_tools
    event_emissions:
      - signal_name: TOOLS_LISTED
"""

# Dynamic tool discovery and invocation pattern
builtin_dynamic_tool_pattern = """
dynamic_tool_workflow:
  DiscoverTools:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_available_tools
    output_field: available_tools
    event_emissions:
      - signal_name: TOOLS_DISCOVERED

  InvokeTool:
    node_type: tool
    event_triggers: [TOOLS_DISCOVERED]
    tool_name: soe_call_tool
    context_parameter_field: tool_invocation
    output_field: invocation_result
    event_emissions:
      - signal_name: INVOCATION_COMPLETE
"""

# --- Identity Management Tools ---

# soe_get_identities - Query identity definitions
builtin_soe_get_identities = """
workflows:
  example_workflow:
    GetIdentities:
      node_type: tool
      event_triggers: [START]
      tool_name: soe_get_identities
      output_field: identities_result
      event_emissions:
        - signal_name: IDENTITIES_RETRIEVED

identities:
  assistant: "You are a helpful assistant."
  expert: "You are an expert programmer."
"""

# soe_get_identities with specific identity
builtin_soe_get_identities_specific = """
workflows:
  example_workflow:
    GetSpecificIdentity:
      node_type: tool
      event_triggers: [START]
      tool_name: soe_get_identities
      context_parameter_field: identity_params
      output_field: identity_result
      event_emissions:
        - signal_name: IDENTITY_RETRIEVED

identities:
  assistant: "You are a helpful assistant."
  expert: "You are an expert programmer."
"""

# soe_inject_identity - Add or update an identity
builtin_soe_inject_identity = """
example_workflow:
  InjectIdentity:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_identity
    context_parameter_field: identity_to_inject
    output_field: injection_result
    event_emissions:
      - signal_name: IDENTITY_INJECTED
"""

# soe_remove_identity - Remove an identity
builtin_soe_remove_identity = """
workflows:
  example_workflow:
    RemoveIdentity:
      node_type: tool
      event_triggers: [START]
      tool_name: soe_remove_identity
      context_parameter_field: identity_to_remove
      output_field: removal_result
      event_emissions:
        - signal_name: IDENTITY_REMOVED

identities:
  old_identity: "This will be removed."
  keep_identity: "This stays."
"""

# Identity management pattern - inject then verify
builtin_identity_management_pattern = """
identity_workflow:
  InjectNewIdentity:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_identity
    context_parameter_field: new_identity
    output_field: inject_result
    event_emissions:
      - signal_name: IDENTITY_CREATED

  VerifyIdentity:
    node_type: tool
    event_triggers: [IDENTITY_CREATED]
    tool_name: soe_get_identities
    output_field: all_identities
    event_emissions:
      - signal_name: IDENTITIES_VERIFIED
"""

# --- Context Schema Management Tools ---

# soe_get_context_schema - Query context schema
builtin_soe_get_context_schema = """
workflows:
  example_workflow:
    GetSchema:
      node_type: tool
      event_triggers: [START]
      tool_name: soe_get_context_schema
      output_field: schema_result
      event_emissions:
        - signal_name: SCHEMA_RETRIEVED

context_schema:
  name:
    type: string
    description: "User name"
  age:
    type: integer
    description: "User age"
"""

# soe_get_context_schema with specific field
builtin_soe_get_context_schema_field = """
workflows:
  example_workflow:
    GetSchemaField:
      node_type: tool
      event_triggers: [START]
      tool_name: soe_get_context_schema
      context_parameter_field: schema_params
      output_field: field_result
      event_emissions:
        - signal_name: FIELD_RETRIEVED

context_schema:
  name:
    type: string
    description: "User name"
  age:
    type: integer
    description: "User age"
"""

# soe_inject_context_schema_field - Add or update a schema field
builtin_soe_inject_context_schema_field = """
example_workflow:
  InjectSchemaField:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_context_schema_field
    context_parameter_field: field_to_inject
    output_field: injection_result
    event_emissions:
      - signal_name: FIELD_INJECTED
"""

# soe_remove_context_schema_field - Remove a schema field
builtin_soe_remove_context_schema_field = """
workflows:
  example_workflow:
    RemoveSchemaField:
      node_type: tool
      event_triggers: [START]
      tool_name: soe_remove_context_schema_field
      context_parameter_field: field_to_remove
      output_field: removal_result
      event_emissions:
        - signal_name: FIELD_REMOVED

context_schema:
  old_field:
    type: string
    description: "This will be removed"
  keep_field:
    type: integer
    description: "This stays"
"""

# Schema management pattern - inject then verify
builtin_schema_management_pattern = """
schema_workflow:
  InjectNewField:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_context_schema_field
    context_parameter_field: new_field
    output_field: inject_result
    event_emissions:
      - signal_name: FIELD_CREATED

  VerifySchema:
    node_type: tool
    event_triggers: [FIELD_CREATED]
    tool_name: soe_get_context_schema
    output_field: full_schema
    event_emissions:
      - signal_name: SCHEMA_VERIFIED
"""
