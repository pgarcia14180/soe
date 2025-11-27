"""
Workflow definitions for Building Custom Workflows

These workflows demonstrate how to combine the three core node types (Tool, LLM, Router)
to build sophisticated patterns like chain-of-thought, custom ReAct loops, and more.

This is the power of SOE: any agent pattern can be built from primitives.
"""

# Pattern 1: Chain of Thought
# Break complex reasoning into explicit steps
chain_of_thought = """
example_workflow:
  Understand:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this problem and restate it in your own words: {{ context.problem }}"
    output_field: understanding
    event_emissions:
      - signal_name: UNDERSTOOD

  Plan:
    node_type: llm
    event_triggers: [UNDERSTOOD]
    prompt: |
      Based on your understanding: {{ context.understanding }}

      Create a step-by-step plan to solve this problem.
    output_field: plan
    event_emissions:
      - signal_name: PLANNED

  Execute:
    node_type: llm
    event_triggers: [PLANNED]
    prompt: |
      Understanding: {{ context.understanding }}
      Plan: {{ context.plan }}

      Now execute the plan and provide the final answer.
    output_field: answer
    event_emissions:
      - signal_name: COMPLETE
"""

# Pattern 2: Custom ReAct Loop
# Build your own Reasoning + Acting loop
custom_react_loop = """
example_workflow:
  Reason:
    node_type: llm
    event_triggers: [START, TOOL_RESULT]
    prompt: |
      Task: {{ context.task }}
      {% if context.tool_results %}
      Previous tool results: {{ context.tool_results }}
      {% endif %}

      Decide what to do next. If you need to use a tool, output:
      {"action": "use_tool", "tool": "tool_name", "args": {...}}

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
        condition: "{{ context.decision.action == 'use_tool' }}"
      - signal_name: FINISH
        condition: "{{ context.decision.action == 'finish' }}"

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
"""

# Pattern 3: Metacognition (Self-Reflection)
# Have the LLM review and critique its own output
metacognition = """
example_workflow:
  Generate:
    node_type: llm
    event_triggers: [START]
    prompt: "Write a response to: {{ context.request }}"
    output_field: draft
    event_emissions:
      - signal_name: DRAFT_READY

  Critique:
    node_type: llm
    event_triggers: [DRAFT_READY]
    prompt: |
      Review this response for errors, unclear language, or improvements:
      {{ context.draft }}

      Output JSON with needs_revision (true or false) and critique fields.
    output_field: review
    event_emissions:
      - signal_name: REVIEWED

  CheckRevision:
    node_type: router
    event_triggers: [REVIEWED]
    event_emissions:
      - signal_name: REVISE
        condition: "{{ context.review.needs_revision == true }}"
      - signal_name: FINALIZE
        condition: "{{ context.review.needs_revision == false }}"

  Refine:
    node_type: llm
    event_triggers: [REVISE]
    prompt: |
      Original: {{ context.draft }}
      Critique: {{ context.review.critique }}

      Write an improved version addressing the feedback.
    output_field: final_response
    event_emissions:
      - signal_name: COMPLETE

  AcceptDraft:
    node_type: router
    event_triggers: [FINALIZE]
    event_emissions:
      - signal_name: COMPLETE
"""

# Pattern 4: Parallel Analysis with Voting
# Run multiple analyses and aggregate results
parallel_voting = """
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
      Check if this content is safe: {{ context.content }}
      Return JSON with safe (boolean) and reason (string) fields.
    output_field: safety_result
    event_emissions:
      - signal_name: SAFETY_DONE

  QualityCheck:
    node_type: llm
    event_triggers: [ANALYZE_QUALITY]
    prompt: |
      Rate the quality of this content: {{ context.content }}
      Return JSON with score (1-10) and feedback (string) fields.
    output_field: quality_result
    event_emissions:
      - signal_name: QUALITY_DONE

  RelevanceCheck:
    node_type: llm
    event_triggers: [ANALYZE_RELEVANCE]
    prompt: |
      Check relevance to topic '{{ context.topic }}': {{ context.content }}
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
        condition: "{{ result.approved == true }}"
      - signal_name: REJECTED
        condition: "{{ result.approved == false }}"
"""

# Pattern 5: Iterative Refinement
# Generate, validate, loop until valid
iterative_refinement = """
example_workflow:
  Generate:
    node_type: llm
    event_triggers: [START, RETRY]
    prompt: |
      Generate Python code for: {{ context.task }}
      {% if context.errors %}
      Previous attempt had these errors: {{ context.errors }}
      Fix them in this attempt.
      {% endif %}
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
        condition: "{{ result.errors|length == 0 }}"
      - signal_name: INVALID
        condition: "{{ result.errors|length > 0 }}"

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
"""

# Pattern 6: Hierarchical Task Decomposition
# Break complex tasks into subtasks
hierarchical_decomposition = """
example_workflow:
  Decompose:
    node_type: llm
    event_triggers: [START]
    prompt: |
      Break this task into subtasks: {{ context.task }}
      Output JSON with subtasks array and types array (research, code, writing).
    output_field: breakdown
    event_emissions:
      - signal_name: DECOMPOSED

  RouteSubtasks:
    node_type: router
    event_triggers: [DECOMPOSED]
    event_emissions:
      - signal_name: DO_RESEARCH
        condition: "{{ 'research' in context.breakdown.types }}"
      - signal_name: DO_CODING
        condition: "{{ 'code' in context.breakdown.types }}"
      - signal_name: DO_WRITING
        condition: "{{ 'writing' in context.breakdown.types }}"

  ResearchSubtask:
    node_type: llm
    event_triggers: [DO_RESEARCH]
    prompt: "Research: {{ context.breakdown.subtasks | selectattr('type', 'equalto', 'research') | list }}"
    output_field: research_result
    event_emissions:
      - signal_name: SUBTASK_DONE

  CodingSubtask:
    node_type: llm
    event_triggers: [DO_CODING]
    prompt: "Code: {{ context.breakdown.subtasks | selectattr('type', 'equalto', 'code') | list }}"
    output_field: code_result
    event_emissions:
      - signal_name: SUBTASK_DONE

  Synthesize:
    node_type: llm
    event_triggers: [SUBTASK_DONE]
    prompt: |
      Combine these results into a final answer:
      Research: {{ context.research_result }}
      Code: {{ context.code_result }}
    output_field: final_answer
    event_emissions:
      - signal_name: COMPLETE
"""
