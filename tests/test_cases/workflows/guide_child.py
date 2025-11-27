"""
Workflow definitions for Child Nodes (Suborchestration)

These workflows are used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)

Child nodes enable modular workflow composition through sub-orchestration.
Parent workflows can spawn child workflows, pass data, receive results,
and share identity for conversation history.
"""

# Simple child - spawn a sub-workflow
CHILD_SIMPLE_EXAMPLE = """
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: child_workflow
    child_initial_signals: [START]
    signals_to_parent: [CHILD_DONE]

  ChildDoneHandler:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

child_workflow:
  DoWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: WORK_COMPLETE

  Finish:
    node_type: router
    event_triggers: [WORK_COMPLETE]
    event_emissions:
      - signal_name: CHILD_DONE
"""

# Child with input fields - pass data to child
CHILD_INPUT_FIELDS_EXAMPLE = """
parent_workflow:
  SpawnProcessor:
    node_type: child
    event_triggers: [START]
    child_workflow_name: processor_workflow
    child_initial_signals: [START]
    input_fields: [data_to_process]
    signals_to_parent: [PROCESSED]

  ProcessedHandler:
    node_type: router
    event_triggers: [PROCESSED]
    event_emissions:
      - signal_name: PARENT_COMPLETE

processor_workflow:
  ProcessData:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PROCESSED
        condition: "{{ context.data_to_process is defined }}"
"""

# Child with context updates - receive data from child
CHILD_CONTEXT_UPDATES_EXAMPLE = """
parent_workflow:
  SpawnCalculator:
    node_type: child
    event_triggers: [START]
    child_workflow_name: calculator_workflow
    child_initial_signals: [START]
    input_fields: [calc_params]
    signals_to_parent: [CALCULATION_DONE]
    context_updates_to_parent: [result]

  ResultHandler:
    node_type: router
    event_triggers: [CALCULATION_DONE]
    event_emissions:
      - signal_name: PARENT_COMPLETE

calculator_workflow:
  Calculate:
    node_type: tool
    event_triggers: [START]
    tool_name: sum_numbers
    context_parameter_field: calc_params
    output_field: result
    event_emissions:
      - signal_name: CALCULATION_DONE
"""

# Child continues after callback - not a "done" signal
CHILD_CONTINUES_EXAMPLE = """
parent_workflow:
  SpawnWorker:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    signals_to_parent: [PROGRESS, COMPLETED]

  ProgressHandler:
    node_type: router
    event_triggers: [PROGRESS]
    event_emissions:
      - signal_name: PROGRESS_LOGGED

  CompleteHandler:
    node_type: router
    event_triggers: [COMPLETED]
    event_emissions:
      - signal_name: ALL_DONE

worker_workflow:
  Phase1:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PHASE1_DONE

  ReportProgress:
    node_type: router
    event_triggers: [PHASE1_DONE]
    event_emissions:
      - signal_name: PROGRESS

  Phase2:
    node_type: router
    event_triggers: [PROGRESS]
    event_emissions:
      - signal_name: PHASE2_DONE

  ReportComplete:
    node_type: router
    event_triggers: [PHASE2_DONE]
    event_emissions:
      - signal_name: COMPLETED
"""

# Multiple children - parallel sub-workflows
MULTIPLE_CHILDREN_EXAMPLE = """
parent_workflow:
  SpawnWorkerA:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_a
    child_initial_signals: [START]
    signals_to_parent: [A_DONE]

  SpawnWorkerB:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_b
    child_initial_signals: [START]
    signals_to_parent: [B_DONE]

  WaitForBoth:
    node_type: router
    event_triggers: [A_DONE, B_DONE]
    event_emissions:
      - signal_name: ALL_WORKERS_DONE

worker_a:
  DoWorkA:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: A_DONE

worker_b:
  DoWorkB:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: B_DONE
"""

# Nested children - grandchild workflows
NESTED_CHILDREN_EXAMPLE = """
main_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: child_workflow
    child_initial_signals: [START]
    signals_to_parent: [CHILD_COMPLETE]

  MainDone:
    node_type: router
    event_triggers: [CHILD_COMPLETE]
    event_emissions:
      - signal_name: MAIN_COMPLETE

child_workflow:
  SpawnGrandchild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: grandchild_workflow
    child_initial_signals: [START]
    signals_to_parent: [GRANDCHILD_DONE]

  ChildDone:
    node_type: router
    event_triggers: [GRANDCHILD_DONE]
    event_emissions:
      - signal_name: CHILD_COMPLETE

grandchild_workflow:
  DoDeepWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GRANDCHILD_DONE
"""

# Child with LLM - sub-workflow with AI
CHILD_WITH_LLM_EXAMPLE = """
parent_workflow:
  SpawnAnalyzer:
    node_type: child
    event_triggers: [START]
    child_workflow_name: analyzer_workflow
    child_initial_signals: [START]
    input_fields: [textToAnalyze]
    signals_to_parent: [ANALYSIS_COMPLETE]
    context_updates_to_parent: [analysisResult]

  AnalysisDone:
    node_type: router
    event_triggers: [ANALYSIS_COMPLETE]
    event_emissions:
      - signal_name: PARENT_DONE

analyzer_workflow:
  AnalyzeText:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this text: {{ context.textToAnalyze }}"
    output_field: analysisResult
    event_emissions:
      - signal_name: ANALYSIS_COMPLETE
"""


# Child with shared conversation history - parent and child share LLM history
# This demonstrates persistent identity across sub-orchestration
CHILD_SHARED_HISTORY = """
parent_workflow:
  ParentLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: shared_session
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: parentResponse
    event_emissions:
      - signal_name: PARENT_LLM_DONE

  SpawnChildWithHistory:
    node_type: child
    event_triggers: [PARENT_LLM_DONE]
    child_workflow_name: child_with_llm
    child_initial_signals: [START]
    input_fields: [follow_up]
    signals_to_parent: [CHILD_LLM_DONE]
    context_updates_to_parent: [childResponse]

  ParentComplete:
    node_type: router
    event_triggers: [CHILD_LLM_DONE]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

child_with_llm:
  ChildLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: shared_session
    prompt: "Continue the conversation. User asks: {{ context.follow_up }}"
    output_field: childResponse
    event_emissions:
      - signal_name: CHILD_LLM_DONE
"""


# Nested children with shared history - grandchild sees parent's history
NESTED_SHARED_HISTORY = """
main_workflow:
  MainLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: deep_session
    prompt: "Start discussing {{ context.topic }}"
    output_field: mainResponse
    event_emissions:
      - signal_name: MAIN_LLM_DONE

  SpawnChild:
    node_type: child
    event_triggers: [MAIN_LLM_DONE]
    child_workflow_name: middle_workflow
    child_initial_signals: [START]
    input_fields: [follow_up]
    signals_to_parent: [DEEP_COMPLETE]
    context_updates_to_parent: [grandchildResponse]

  MainComplete:
    node_type: router
    event_triggers: [DEEP_COMPLETE]
    event_emissions:
      - signal_name: ALL_DONE

middle_workflow:
  SpawnGrandchild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: grandchild_llm_workflow
    child_initial_signals: [START]
    input_fields: [follow_up]
    signals_to_parent: [GRANDCHILD_LLM_DONE]
    context_updates_to_parent: [grandchildResponse]

  MiddleDone:
    node_type: router
    event_triggers: [GRANDCHILD_LLM_DONE]
    event_emissions:
      - signal_name: DEEP_COMPLETE

grandchild_llm_workflow:
  GrandchildLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: deep_session
    prompt: "Continue the discussion. Question: {{ context.follow_up }}"
    output_field: grandchildResponse
    event_emissions:
      - signal_name: GRANDCHILD_LLM_DONE
"""


# ============================================================================
# MULTI-TURN CHILD IDENTITY WORKFLOWS
# ============================================================================

# Parent has 2 LLM calls, then child has 1 LLM call - all share identity
# Total: 3 LLM calls with shared history
CHILD_THREE_TURN_SHARED_HISTORY = """
parent_workflow:
  ParentTurn1:
    node_type: llm
    event_triggers: [START]
    identity: shared_session
    prompt: "Start a conversation about {{ context.topic }}"
    output_field: parentResponse1
    event_emissions:
      - signal_name: PARENT_TURN1_DONE

  ParentTurn2:
    node_type: llm
    event_triggers: [PARENT_TURN1_DONE]
    identity: shared_session
    prompt: "Continue with follow-up: {{ context.parent_followup }}"
    output_field: parentResponse2
    event_emissions:
      - signal_name: PARENT_TURN2_DONE

  SpawnChildWithHistory:
    node_type: child
    event_triggers: [PARENT_TURN2_DONE]
    child_workflow_name: child_continues_conversation
    child_initial_signals: [START]
    input_fields: [child_question]
    signals_to_parent: [CHILD_DONE]
    context_updates_to_parent: [childResponse]

  ParentComplete:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

child_continues_conversation:
  ChildLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: shared_session
    prompt: "Continue conversation. User asks: {{ context.child_question }}"
    output_field: childResponse
    event_emissions:
      - signal_name: CHILD_DONE
"""

# Parent 1 call, child 2 calls, grandchild 1 call - all share identity
# Total: 4 LLM calls with shared history
NESTED_FOUR_TURN_SHARED_HISTORY = """
main_workflow:
  MainLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: deep_session
    prompt: "Start main discussion about {{ context.topic }}"
    output_field: mainResponse
    event_emissions:
      - signal_name: MAIN_LLM_DONE

  SpawnChild:
    node_type: child
    event_triggers: [MAIN_LLM_DONE]
    child_workflow_name: middle_two_turn_workflow
    child_initial_signals: [START]
    input_fields: [child_msg1, child_msg2, grandchild_msg]
    signals_to_parent: [DEEP_COMPLETE]
    context_updates_to_parent: [childResponse1, childResponse2, grandchildResponse]

  MainComplete:
    node_type: router
    event_triggers: [DEEP_COMPLETE]
    event_emissions:
      - signal_name: ALL_DONE

middle_two_turn_workflow:
  ChildTurn1:
    node_type: llm
    event_triggers: [START]
    identity: deep_session
    prompt: "Continue from main. Question: {{ context.child_msg1 }}"
    output_field: childResponse1
    event_emissions:
      - signal_name: CHILD_TURN1_DONE

  ChildTurn2:
    node_type: llm
    event_triggers: [CHILD_TURN1_DONE]
    identity: deep_session
    prompt: "Follow-up question: {{ context.child_msg2 }}"
    output_field: childResponse2
    event_emissions:
      - signal_name: CHILD_TURN2_DONE

  SpawnGrandchild:
    node_type: child
    event_triggers: [CHILD_TURN2_DONE]
    child_workflow_name: grandchild_single_turn
    child_initial_signals: [START]
    input_fields: [grandchild_msg]
    signals_to_parent: [GRANDCHILD_DONE]
    context_updates_to_parent: [grandchildResponse]

  MiddleDone:
    node_type: router
    event_triggers: [GRANDCHILD_DONE]
    event_emissions:
      - signal_name: DEEP_COMPLETE

grandchild_single_turn:
  GrandchildLLMCall:
    node_type: llm
    event_triggers: [START]
    identity: deep_session
    prompt: "Final question from grandchild: {{ context.grandchild_msg }}"
    output_field: grandchildResponse
    event_emissions:
      - signal_name: GRANDCHILD_DONE
"""


# ============================================================================
# EDGE CASE WORKFLOWS
# ============================================================================

# Child with no signals_to_parent - fire and forget
CHILD_FIRE_AND_FORGET = """
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: background_worker
    child_initial_signals: [START]

  ParentContinues:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PARENT_DONE

background_worker:
  DoBackgroundWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: WORK_DONE
"""

# Child with missing child_workflow_name - should handle gracefully
CHILD_MISSING_WORKFLOW_NAME = """
parent_workflow:
  SpawnMissing:
    node_type: child
    event_triggers: [START]
    child_workflow_name: nonexistent_workflow
    child_initial_signals: [START]
    signals_to_parent: [CHILD_DONE]

  FallbackHandler:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PARENT_FALLBACK
"""

# Child with empty input_fields list
CHILD_EMPTY_INPUT_FIELDS = """
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: minimal_workflow
    child_initial_signals: [START]
    input_fields: []
    signals_to_parent: [CHILD_DONE]

  ChildDoneHandler:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: PARENT_COMPLETE

minimal_workflow:
  DoWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHILD_DONE
"""

# Child with input_fields referencing missing context
CHILD_MISSING_INPUT_FIELDS = """
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: child_with_optional
    child_initial_signals: [START]
    input_fields: [missing_field, another_missing]
    signals_to_parent: [CHILD_DONE]

  ChildDoneHandler:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: PARENT_COMPLETE

child_with_optional:
  CheckFields:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHILD_DONE
"""

# Child with context_updates referencing field that child doesn't create
CHILD_MISSING_CONTEXT_UPDATE = """
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: child_no_result
    child_initial_signals: [START]
    signals_to_parent: [CHILD_DONE]
    context_updates_to_parent: [nonexistent_result]

  ChildDoneHandler:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: PARENT_COMPLETE

child_no_result:
  DoWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHILD_DONE
"""

# Multiple children with same signals_to_parent - signal deduplication
CHILDREN_SAME_SIGNAL = """
parent_workflow:
  SpawnWorkerA:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_generic
    child_initial_signals: [START]
    signals_to_parent: [WORKER_DONE]

  SpawnWorkerB:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_generic
    child_initial_signals: [START]
    signals_to_parent: [WORKER_DONE]

  CountDone:
    node_type: router
    event_triggers: [WORKER_DONE]
    event_emissions:
      - signal_name: ALL_WORKERS_DONE
        condition: "{{ context.__operational__.signals.count('WORKER_DONE') >= 2 }}"

worker_generic:
  DoWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: WORKER_DONE
"""

# Child spawning itself (recursive) - should be prevented or limited
CHILD_RECURSIVE = """
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: recursive_workflow
    child_initial_signals: [START]
    signals_to_parent: [DONE]

recursive_workflow:
  CheckDepth:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
        condition: "{{ context.depth|default(0) >= 3 }}"
      - signal_name: GO_DEEPER
        condition: "{{ context.depth|default(0) < 3 }}"

  SpawnSelf:
    node_type: child
    event_triggers: [GO_DEEPER]
    child_workflow_name: recursive_workflow
    child_initial_signals: [START]
    signals_to_parent: [DONE]
"""

# Deeply nested children (5 levels)
DEEPLY_NESTED_CHILDREN = """
level1_workflow:
  Spawn:
    node_type: child
    event_triggers: [START]
    child_workflow_name: level2_workflow
    child_initial_signals: [START]
    signals_to_parent: [LEVEL2_DONE]

  Done:
    node_type: router
    event_triggers: [LEVEL2_DONE]
    event_emissions:
      - signal_name: LEVEL1_COMPLETE

level2_workflow:
  Spawn:
    node_type: child
    event_triggers: [START]
    child_workflow_name: level3_workflow
    child_initial_signals: [START]
    signals_to_parent: [LEVEL3_DONE]

  Done:
    node_type: router
    event_triggers: [LEVEL3_DONE]
    event_emissions:
      - signal_name: LEVEL2_DONE

level3_workflow:
  Spawn:
    node_type: child
    event_triggers: [START]
    child_workflow_name: level4_workflow
    child_initial_signals: [START]
    signals_to_parent: [LEVEL4_DONE]

  Done:
    node_type: router
    event_triggers: [LEVEL4_DONE]
    event_emissions:
      - signal_name: LEVEL3_DONE

level4_workflow:
  Spawn:
    node_type: child
    event_triggers: [START]
    child_workflow_name: level5_workflow
    child_initial_signals: [START]
    signals_to_parent: [LEVEL5_DONE]

  Done:
    node_type: router
    event_triggers: [LEVEL5_DONE]
    event_emissions:
      - signal_name: LEVEL4_DONE

level5_workflow:
  DeepWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: LEVEL5_DONE
"""

# Child with different identity than parent - isolated histories
CHILD_DIFFERENT_IDENTITY = """
parent_workflow:
  ParentLLM:
    node_type: llm
    event_triggers: [START]
    identity: parent_session
    prompt: "Start parent conversation about {{ context.topic }}"
    output_field: parentResponse
    event_emissions:
      - signal_name: PARENT_LLM_DONE

  SpawnChild:
    node_type: child
    event_triggers: [PARENT_LLM_DONE]
    child_workflow_name: child_different_id
    child_initial_signals: [START]
    input_fields: [follow_up]
    signals_to_parent: [CHILD_DONE]
    context_updates_to_parent: [childResponse]

  Complete:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

child_different_id:
  ChildLLM:
    node_type: llm
    event_triggers: [START]
    identity: child_session
    prompt: "Start fresh conversation: {{ context.follow_up }}"
    output_field: childResponse
    event_emissions:
      - signal_name: CHILD_DONE
"""
