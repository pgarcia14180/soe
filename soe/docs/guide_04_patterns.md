
# SOE Guide: Chapter 4 - Building Custom Workflows

## The Three Core Node Types

You now know SOE's three core node types:

| Node | What It Does | Key Capability |
|------|--------------|----------------|
| **Tool** | Executes Python functions | Real-world actions |
| **LLM** | Calls language models | Intelligence & generation |
| **Router** | Routes based on context | Control flow & branching |

These three nodes are **all you need** to build sophisticated AI workflows. This chapter shows you how to combine them into powerful patterns—including building your own agent loops from scratch.

## Why Build Custom Workflows?

The built-in **Agent Node** (covered in the next chapter) provides a convenient ReAct loop. But sometimes you need:

- **Custom reasoning patterns** (chain-of-thought, tree-of-thought, metacognition)
- **Fine-grained control** over each step
- **Hybrid logic** mixing deterministic and AI-driven decisions
- **Domain-specific agent architectures**

With these three core nodes, you can build any pattern—the Agent Node is just one opinionated implementation.

---

## Pattern 1: Chain of Thought

**The Pattern**: Break complex reasoning into explicit steps, where each LLM call builds on the previous one.

### The Workflow

```yaml
example_workflow:
  Understand:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this problem and restate it in your own words: &#123;&#123; context.problem &#125;&#125;"
    output_field: understanding
    event_emissions:
      - signal_name: UNDERSTOOD

  Plan:
    node_type: llm
    event_triggers: [UNDERSTOOD]
    prompt: |
      Based on your understanding: &#123;&#123; context.understanding &#125;&#125;

      Create a step-by-step plan to solve this problem.
    output_field: plan
    event_emissions:
      - signal_name: PLANNED

  Execute:
    node_type: llm
    event_triggers: [PLANNED]
    prompt: |
      Understanding: &#123;&#123; context.understanding &#125;&#125;
      Plan: &#123;&#123; context.plan &#125;&#125;

      Now execute the plan and provide the final answer.
    output_field: answer
    event_emissions:
      - signal_name: COMPLETE
```

### How It Works

1. **Understand**: LLM analyzes and restates the problem
2. **Plan**: LLM creates a step-by-step plan based on its understanding
3. **Execute**: LLM generates the final answer using the plan

Each step stores its output in context, and the next step reads it.

### Why This Pattern?

- **Transparency**: Each reasoning step is visible and inspectable
- **Debuggability**: If the answer is wrong, you can see exactly where reasoning failed
- **Control**: You can add validation routers between steps

---

## Pattern 2: Custom ReAct Loop

**The Pattern**: Build your own Reasoning + Acting loop using the three core node types.

### The Workflow

```yaml
example_workflow:
  Reason:
    node_type: llm
    event_triggers: [START, TOOL_RESULT]
    prompt: |
      Task: &#123;&#123; context.task &#125;&#125;
      &#123;% if context.tool_results %&#125;
      Previous tool results: &#123;&#123; context.tool_results &#125;&#125;
      &#123;% endif %&#125;

      Decide what to do next. If you need to use a tool, output:
      {"action": "use_tool", "tool": "tool_name", "args": {...&#125;&#125;

      If you have the final answer, output:
      {"action": "finish", "answer": "your answer"}
    output_field: decision
    event_emissions:
      - signal_name: DECIDED

  Route:
    node_type: router
    event_triggers: [DECIDED]
    event_emissions:
      - signal_name: USE_TOOL
        condition: "&#123;&#123; context.decision.action == 'use_tool' &#125;&#125;"
      - signal_name: FINISH
        condition: "&#123;&#123; context.decision.action == 'finish' &#125;&#125;"

  Act:
    node_type: tool
    event_triggers: [USE_TOOL]
    tool_name: dynamic_tool
    context_parameter_field: decision
    output_field: tool_results
    event_emissions:
      - signal_name: TOOL_RESULT

  Complete:
    node_type: router
    event_triggers: [FINISH]
    event_emissions:
      - signal_name: TASK_COMPLETE
```

### How It Works

1. **Reason**: LLM analyzes the situation and decides what to do
2. **Route**: Router checks if LLM wants to use a tool or finish
3. **Act**: If tool needed, execute it and loop back to Reason
4. **Complete**: When done, emit final signal

### The Loop Structure

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│  │ Reason  │───▶│  Route  │───▶│   Act   │──────────┘
│  │  (LLM)  │    │(Router) │    │ (Tool)  │
│  └─────────┘    └────┬────┘    └─────────┘
│                      │
│                      ▼
│                 ┌─────────┐
│                 │Complete │
│                 │(Router) │
│                 └─────────┘
```

This is exactly what the Agent Node does internally—but now you control every piece.

---

## Pattern 3: Metacognition (Self-Reflection)

**The Pattern**: Have the LLM review and critique its own output before finalizing.

### The Workflow

```yaml
example_workflow:
  Generate:
    node_type: llm
    event_triggers: [START]
    prompt: "Write a response to: &#123;&#123; context.request &#125;&#125;"
    output_field: draft
    event_emissions:
      - signal_name: DRAFT_READY

  Critique:
    node_type: llm
    event_triggers: [DRAFT_READY]
    prompt: |
      Review this response for errors, unclear language, or improvements:
      &#123;&#123; context.draft &#125;&#125;

      Output JSON with needs_revision (true or false) and critique fields.
    output_field: review
    event_emissions:
      - signal_name: REVIEWED

  CheckRevision:
    node_type: router
    event_triggers: [REVIEWED]
    event_emissions:
      - signal_name: REVISE
        condition: "&#123;&#123; context.review.needs_revision == true &#125;&#125;"
      - signal_name: FINALIZE
        condition: "&#123;&#123; context.review.needs_revision == false &#125;&#125;"

  Refine:
    node_type: llm
    event_triggers: [REVISE]
    prompt: |
      Original: &#123;&#123; context.draft &#125;&#125;
      Critique: &#123;&#123; context.review.critique &#125;&#125;

      Write an improved version addressing the feedback.
    output_field: final_response
    event_emissions:
      - signal_name: COMPLETE

  AcceptDraft:
    node_type: router
    event_triggers: [FINALIZE]
    event_emissions:
      - signal_name: COMPLETE
```

### How It Works

1. **Generate**: LLM produces an initial response
2. **Critique**: A second LLM call reviews the response for errors or improvements
3. **Route**: Check if revision is needed
4. **Refine** (if needed): Generate improved response based on critique
5. **Finalize**: Output the best version

### Why This Pattern?

- **Quality improvement**: Catches errors the first pass missed
- **Self-correction**: The model identifies its own weaknesses
- **Controllable iteration**: You decide when to stop refining

---

## Pattern 4: Parallel Analysis with Voting

**The Pattern**: Run multiple LLM analyses in parallel, then aggregate results.

### The Workflow

```yaml
example_workflow:
  FanOut:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ANALYZE_SAFETY
      - signal_name: ANALYZE_QUALITY
      - signal_name: ANALYZE_RELEVANCE

  SafetyCheck:
    node_type: llm
    event_triggers: [ANALYZE_SAFETY]
    prompt: |
      Check if this content is safe: &#123;&#123; context.content &#125;&#125;
      Return JSON with safe (boolean) and reason (string) fields.
    output_field: safety_result
    event_emissions:
      - signal_name: SAFETY_DONE

  QualityCheck:
    node_type: llm
    event_triggers: [ANALYZE_QUALITY]
    prompt: |
      Rate the quality of this content: &#123;&#123; context.content &#125;&#125;
      Return JSON with score (1-10) and feedback (string) fields.
    output_field: quality_result
    event_emissions:
      - signal_name: QUALITY_DONE

  RelevanceCheck:
    node_type: llm
    event_triggers: [ANALYZE_RELEVANCE]
    prompt: |
      Check relevance to topic '&#123;&#123; context.topic &#125;&#125;': &#123;&#123; context.content &#125;&#125;
      Return JSON with relevant (boolean) field.
    output_field: relevance_result
    event_emissions:
      - signal_name: RELEVANCE_DONE

  Aggregate:
    node_type: tool
    event_triggers: [SAFETY_DONE, QUALITY_DONE, RELEVANCE_DONE]
    tool_name: aggregate_votes
    context_parameter_field: vote_params
    output_field: final_decision
    event_emissions:
      - signal_name: APPROVED
        condition: "&#123;&#123; result.approved == true &#125;&#125;"
      - signal_name: REJECTED
        condition: "&#123;&#123; result.approved == false &#125;&#125;"
```

### How It Works

1. **Fan-Out**: Router emits multiple signals simultaneously
2. **Parallel Analysis**: Multiple LLM nodes run independently
3. **Aggregate**: Tool collects all analyses and determines consensus
4. **Route Result**: Based on the aggregated vote

### Why This Pattern?

- **Diversity of perspective**: Different prompts catch different issues
- **Robustness**: Single LLM errors are outvoted
- **Speed**: Parallel execution (if your infrastructure supports it)

---

## Pattern 5: Iterative Refinement with Tools

**The Pattern**: LLM generates, tool validates, loop until valid.

### The Workflow

```yaml
example_workflow:
  Generate:
    node_type: llm
    event_triggers: [START, RETRY]
    prompt: |
      Generate Python code for: &#123;&#123; context.task &#125;&#125;
      &#123;% if context.errors %&#125;
      Previous attempt had these errors: &#123;&#123; context.errors &#125;&#125;
      Fix them in this attempt.
      &#123;% endif %&#125;
    output_field: code
    event_emissions:
      - signal_name: CODE_GENERATED

  Validate:
    node_type: tool
    event_triggers: [CODE_GENERATED]
    tool_name: lint_code
    context_parameter_field: code
    output_field: validation
    event_emissions:
      - signal_name: VALID
        condition: "&#123;&#123; result.errors|length == 0 &#125;&#125;"
      - signal_name: INVALID
        condition: "&#123;&#123; result.errors|length > 0 &#125;&#125;"

  PrepareRetry:
    node_type: router
    event_triggers: [INVALID]
    event_emissions:
      - signal_name: RETRY

  Complete:
    node_type: router
    event_triggers: [VALID]
    event_emissions:
      - signal_name: CODE_COMPLETE
```

### How It Works

1. **Generate**: LLM creates code/content
2. **Validate**: Tool runs linter, tests, or other validation
3. **Route**: Check validation result
4. **Loop or Complete**: If invalid, inject errors and regenerate

### The Loop Structure

```
┌────────────────────────────────────────────────┐
│                                                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Generate │───▶│ Validate │───▶│  Route   │─┘
│  │  (LLM)   │    │  (Tool)  │    │ (Router) │
│  └──────────┘    └──────────┘    └────┬─────┘
│                                       │
│                                       ▼
│                                 ┌──────────┐
│                                 │ Complete │
│                                 └──────────┘
```

---

## Pattern 6: Hierarchical Task Decomposition

**The Pattern**: Break complex tasks into subtasks, solve each, then synthesize.

### The Workflow

```yaml
example_workflow:
  Decompose:
    node_type: llm
    event_triggers: [START]
    prompt: |
      Break this task into subtasks: &#123;&#123; context.task &#125;&#125;
      Output JSON with subtasks array and types array (research, code, writing).
    output_field: breakdown
    event_emissions:
      - signal_name: DECOMPOSED

  RouteSubtasks:
    node_type: router
    event_triggers: [DECOMPOSED]
    event_emissions:
      - signal_name: DO_RESEARCH
        condition: "&#123;&#123; 'research' in context.breakdown.types &#125;&#125;"
      - signal_name: DO_CODING
        condition: "&#123;&#123; 'code' in context.breakdown.types &#125;&#125;"
      - signal_name: DO_WRITING
        condition: "&#123;&#123; 'writing' in context.breakdown.types &#125;&#125;"

  ResearchSubtask:
    node_type: llm
    event_triggers: [DO_RESEARCH]
    prompt: "Research: &#123;&#123; context.breakdown.subtasks | selectattr('type', 'equalto', 'research') | list &#125;&#125;"
    output_field: research_result
    event_emissions:
      - signal_name: SUBTASK_DONE

  CodingSubtask:
    node_type: llm
    event_triggers: [DO_CODING]
    prompt: "Code: &#123;&#123; context.breakdown.subtasks | selectattr('type', 'equalto', 'code') | list &#125;&#125;"
    output_field: code_result
    event_emissions:
      - signal_name: SUBTASK_DONE

  Synthesize:
    node_type: llm
    event_triggers: [SUBTASK_DONE]
    prompt: |
      Combine these results into a final answer:
      Research: &#123;&#123; context.research_result &#125;&#125;
      Code: &#123;&#123; context.code_result &#125;&#125;
    output_field: final_answer
    event_emissions:
      - signal_name: COMPLETE
```

### How It Works

1. **Decompose**: LLM breaks the task into subtasks
2. **Fan-Out**: Router emits signals for each subtask type
3. **Solve**: Specialized nodes handle each subtask
4. **Synthesize**: Combine subtask results into final answer

---

## Combining Patterns

The real power comes from combining patterns. For example:

- **Chain-of-Thought + Metacognition**: Reason step-by-step, then self-review
- **Custom ReAct + Iterative Refinement**: Agent loop with validation gates
- **Parallel Voting + Hierarchical Decomposition**: Ensemble of specialized agents

Since everything is YAML, you can compose patterns freely.

---

## When to Use Custom Workflows vs Agent Node

| Use Custom Workflows When... | Use Agent Node When... |
|------------------------------|------------------------|
| You need non-standard reasoning patterns | Standard ReAct loop is sufficient |
| You want explicit control over each step | You want hands-off tool-using agent |
| You're debugging or iterating on agent logic | You need quick prototyping |
| You need deterministic checkpoints | Tool selection is the main complexity |
| You're building production systems with audit requirements | Development speed matters most |

The Agent Node is a **convenience**—it encapsulates a common pattern. These custom workflows show you can build anything.

---

## Next Steps

Now that you can build custom agent patterns, see how the built-in [Agent Node](guide_05_agent.md) encapsulates the ReAct pattern for convenience →
