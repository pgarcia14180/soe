
# SOE Guide: Chapter 11 - Built-in Tools

## The Power of Self-Evolution

SOE includes a set of **built-in tools** that are always available to your workflows. These aren't ordinary utilities—they're the foundation for **self-evolving systems**.

Built-in tools enable workflows to:

- **Explore their own documentation** — Understand what they can do
- **Modify workflows at runtime** — Inject, remove, or reconfigure nodes
- **Manage execution context** — Read, update, and copy context data
- **Query available capabilities** — Discover registered tools dynamically

---

## Naming Convention

All built-in tools use the `soe_` prefix to clearly distinguish them from user-defined tools. This prevents naming conflicts and makes it clear these are system-provided utilities.

---

## Principles

### Always Available

Built-in tools require no registration. Simply reference them by name in any tool node:

```yaml
example_workflow:
  ExploreDocs:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: docs_list
    event_emissions:
      - signal_name: DOCS_LISTED
```

### Essential for Self-Evolution

These tools are the building blocks for autonomous systems. An LLM can:

1. **Read documentation** to understand capabilities
2. **Query workflows** to see current structure
3. **Inject new nodes** to extend behavior
4. **Manage context** to persist learned patterns

### No Registration Required

Unlike custom tools that need a `tools_registry`, built-ins work immediately. SOE provides them automatically during orchestration.

---

## Available Built-ins

| Built-in | Purpose | Documentation |
|----------|---------|---------------|
| `soe_explore_docs` | Make SOE self-aware by exploring its documentation | [explore_docs](builtins/soe_explore_docs.md) |
| `soe_get_workflows` | Query registered workflow definitions | [workflows](builtins/workflows.md) |
| `soe_inject_workflow` | Add new workflows at runtime | [workflows](builtins/workflows.md) |
| `soe_inject_node` | Add or modify nodes in workflows | [workflows](builtins/workflows.md) |
| `soe_remove_workflow` | Remove workflows from registry | [workflows](builtins/workflows.md) |
| `soe_remove_node` | Remove nodes from workflows | [workflows](builtins/workflows.md) |
| `soe_add_signal` | Add signals to node configurations | [workflows](builtins/workflows.md) |
| `soe_get_context` | Read execution context | [context](builtins/context.md) |
| `soe_update_context` | Modify execution context | [context](builtins/context.md) |
| `soe_copy_context` | Clone context for parallel execution | [context](builtins/context.md) |
| `soe_list_contexts` | Discover available contexts | [context](builtins/context.md) |
| `soe_get_identities` | Query identity definitions | [identity](builtins/identity.md) |
| `soe_inject_identity` | Add or update an identity | [identity](builtins/identity.md) |
| `soe_remove_identity` | Remove an identity | [identity](builtins/identity.md) |
| `soe_get_context_schema` | Query context schema | [context_schema](builtins/context_schema.md) |
| `soe_inject_context_schema_field` | Add or update a schema field | [context_schema](builtins/context_schema.md) |
| `soe_remove_context_schema_field` | Remove a schema field | [context_schema](builtins/context_schema.md) |
| `soe_get_available_tools` | List all registered tools | [tools](builtins/tools.md) |
| `soe_call_tool` | Invoke a tool by name dynamically | [tools](builtins/tools.md) |

---

## Self-Awareness in Practice

Here's a workflow that becomes self-aware by exploring docs and querying its own state:

```yaml
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
```

This pattern is the foundation for metacognitive workflows that can reason about their own capabilities.

---

## Next Steps

Explore each built-in category in detail:

- **[explore_docs](builtins/soe_explore_docs.md)** — Self-awareness through documentation
- **[workflows](builtins/workflows.md)** — Runtime workflow modification
- **[context](builtins/context.md)** — Execution state management
- **[identity](builtins/identity.md)** — Runtime identity management
- **[context_schema](builtins/context_schema.md)** — Runtime schema management
- **[tools](builtins/tools.md)** — Dynamic tool discovery and invocation

---

## Related

- [Advanced Patterns](advanced_patterns/index.md) — Complex workflow patterns
- [Self-Evolving Workflows](advanced_patterns/self_evolving_workflows.md) — Full self-evolution guide
