
# Built-in: soe_explore_docs

## Making SOE Self-Aware

The `soe_explore_docs` built-in tool enables workflows to **explore their own documentation**. This is the foundation for self-awareness—a workflow can discover what SOE is capable of, understand its own structure, and reason about available patterns.

---

## Why Self-Awareness Matters

Self-awareness transforms a static workflow into an intelligent system that can:

- **Discover capabilities** — Find out what node types, patterns, and features exist
- **Learn from examples** — Read documentation to understand how to use features
- **Adapt behavior** — Make decisions based on available functionality
- **Evolve intelligently** — Create new nodes based on documented patterns

Without `soe_explore_docs`, an LLM in a workflow would be "blind"—it couldn't know what SOE can do. With it, the LLM becomes a partner that understands the orchestration engine itself.

---

## Basic Usage

### List Documentation Structure

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

Returns entries like:
```
[DIR] advanced_patterns/
[FILE] guide_01_tool.md
[FILE] guide_02_llm.md
```

### Search Documentation

```yaml
example_workflow:
  SearchDocs:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: search_results
    event_emissions:
      - signal_name: SEARCH_COMPLETE
```

Search finds relevant paths matching the query.

### Read Documentation Content

```yaml
example_workflow:
  ReadGuide:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    context_parameter_field: explore_params
    output_field: guide_content
    event_emissions:
      - signal_name: GUIDE_READ
```

Returns the full markdown content of the file.

---

## Actions Reference

| Action | Description | Required Args |
|--------|-------------|---------------|
| `list` | Show children at path (files, dirs, sections) | `path` |
| `read` | Get content of file or section | `path` |
| `tree` | Recursive structure from path | `path` |
| `search` | Find docs matching query/tag | `query` or `tag` |
| `get_tags` | List all available tags | none |

---

## Path Navigation

The `path` argument navigates the documentation hierarchy:

| Path | What It Returns |
|------|-----------------|
| `/` | Root documentation listing |
| `soe/docs/guide_01_tool.md` | File content or sections within |
| `soe/docs/guide_01_tool.md/Your First Tool Node` | Specific section content |
| `soe/docs/advanced_patterns/` | Directory contents |

---

## Integration with LLM Nodes

The power of `soe_explore_docs` comes from combining it with LLM reasoning:

```yaml
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
```

---

## Related

- [Built-in Tools Overview](../guide_11_builtins.md) — All available built-ins
- [Self-Evolving Workflows](../advanced_patterns/self_evolving_workflows.md) — Using soe_explore_docs for evolution
