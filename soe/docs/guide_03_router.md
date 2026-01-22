
# SOE Guide: Chapter 3 - Router Nodes

## Introduction to Router Nodes

The **Router** is a pure routing node—it doesn't execute code or call LLMs. It simply reads the context, evaluates conditions, and emits signals to direct the workflow.

Think of a Router as a **traffic controller**: based on the current state (context), it decides which signal to emit, directing the workflow to the next step. Routers are the glue that connects your Tool and LLM nodes together.

### When to Use Router Nodes

- **Entry Points**: Start a workflow and fan out to multiple paths
- **Conditional Branching**: Route based on context values
- **Signal Transformation**: Convert one signal to another
- **Checkpoints**: Create explicit decision points in your workflow

### Why Router Comes Third

We covered Tool and LLM nodes first because they **do work**. Routers don't—they route. Now that you understand the nodes that execute, you can see how Routers connect them into powerful workflows.

## Your First Router: Input Validation

Let's validate that user input exists before processing it.

### The Workflow

```yaml
example_workflow:
  InputValidator:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID_INPUT
        condition: "&#123;&#123; context.user_input is defined and context.user_input != '' &#125;&#125;"
      - signal_name: INVALID_INPUT
        condition: "&#123;&#123; context.user_input is not defined or context.user_input == '' &#125;&#125;"
```

### How It Works

1. **Event Trigger**: The `START` signal triggers the `InputValidator` node.
2. **Condition Evaluation**: The router checks two conditions using Jinja2 templates:
   - If `context.user_input` is defined and not empty → emit `VALID_INPUT`
   - If `context.user_input` is missing or empty → emit `INVALID_INPUT`
3. **Signal Emission**: One or more signals are emitted based on which conditions are true.

### Key Concepts

- **Routers** evaluate Jinja2 conditions and emit signals
- **Conditions** can check if variables exist, compare values, etc.
- **Signals** are the "nervous system" of SOE—they trigger the next steps

## Unconditional Signals

Not every router needs a condition. Sometimes you just want to forward a signal unconditionally.

### The Workflow

```yaml
example_workflow:
  Forwarder:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CONTINUE
```

This router simply receives `START` and immediately emits `CONTINUE`. It's useful when you want to:
- **Rename signals**: Transform external signals to internal naming
- **Create checkpoints**: Make workflow structure explicit
- **Fan-out**: Emit multiple signals to trigger parallel processing

## Decision Trees: Routers Calling Routers

The real power of routers emerges when you chain them together. Since each router emits signals that trigger other nodes, you can build **decision trees** (or more generally, **directed graphs**) where the workflow branches based on context.

### The Pattern

Think of it as a flowchart:
- **Level 1 Router**: Classifies the initial request
- **Level 2+ Routers**: Handle sub-cases, triggered by signals from Level 1
- **Terminal Nodes**: Complete specific branches of the tree

### The Workflow

```yaml
example_workflow:
  # Level 1: Is the user premium or free?
  UserTierCheck:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PREMIUM_PATH
        condition: "&#123;&#123; context.user_tier == 'premium' &#125;&#125;"
      - signal_name: FREE_PATH
        condition: "&#123;&#123; context.user_tier == 'free' &#125;&#125;"

  # Level 2a: Premium users get feature checks
  PremiumFeatureRouter:
    node_type: router
    event_triggers: [PREMIUM_PATH]
    event_emissions:
      - signal_name: ENABLE_ADVANCED
        condition: "&#123;&#123; context.feature_level == 'advanced' &#125;&#125;"
      - signal_name: ENABLE_BASIC
        condition: "&#123;&#123; context.feature_level != 'advanced' &#125;&#125;"

  # Level 2b: Free users get upgrade prompts
  FreeUserRouter:
    node_type: router
    event_triggers: [FREE_PATH]
    event_emissions:
      - signal_name: SHOW_UPGRADE
        condition: "&#123;&#123; context.show_upsell &#125;&#125;"
      - signal_name: CONTINUE_FREE
        condition: "&#123;&#123; not context.show_upsell &#125;&#125;"
```

### How It Works

1. `UserTierCheck` receives `START` and evaluates `context.user_tier`
2. Depending on the tier, it emits either `PREMIUM_PATH` or `FREE_PATH`
3. The corresponding router (`PremiumFeatureRouter` or `FreeUserRouter`) activates
4. That router evaluates its own conditions and emits the final signal

### Why This Matters

- **Modularity**: Each router handles one decision. Easy to test, easy to modify.
- **Composition**: Add new branches by adding new routers—no need to modify existing ones.
- **Visibility**: The workflow YAML *is* the flowchart. No hidden logic in code.

## The Three Core Node Types

You now know the three core node types in SOE:

| Node | Purpose | Does Work? |
|------|---------|-----------|
| **Tool** | Execute Python functions | ✅ Yes |
| **LLM** | Call language models | ✅ Yes |
| **Router** | Route signals based on context | ❌ No (pure routing) |

With just these three nodes, you can build remarkably sophisticated workflows—including custom agent patterns, chain-of-thought reasoning, and more. The next chapter shows you how.

## Next Steps

Now that you understand the three core node types, let's combine them into powerful patterns with [Building Custom Workflows](guide_04_patterns.md) →
