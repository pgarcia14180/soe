"""
Workflow definitions for Advanced Patterns: Swarm Intelligence

These workflows demonstrate:
1. Multi-agent voting/consensus
2. Signal-based counting and aggregation
3. Jury pattern for decision making

Used by both:
1. Test cases (imported and executed)
2. Documentation (extracted via Jinja2)
"""

# =============================================================================
# SIMPLE VOTING: Multiple agents vote, router tallies
# =============================================================================

# Three agents analyze content and vote
voting_workflow = """
voting_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ANALYZE

  # Three "voters" - each is an LLM that outputs a verdict
  Voter1:
    node_type: llm
    event_triggers: [ANALYZE]
    prompt: |
      Analyze if this content is appropriate: {{ context.content }}
      You must output either "approve" or "reject".
    output_field: vote_1
    event_emissions:
      - signal_name: VOTE_CAST

  Voter2:
    node_type: llm
    event_triggers: [ANALYZE]
    prompt: |
      Analyze if this content is appropriate: {{ context.content }}
      You must output either "approve" or "reject".
    output_field: vote_2
    event_emissions:
      - signal_name: VOTE_CAST

  Voter3:
    node_type: llm
    event_triggers: [ANALYZE]
    prompt: |
      Analyze if this content is appropriate: {{ context.content }}
      You must output either "approve" or "reject".
    output_field: vote_3
    event_emissions:
      - signal_name: VOTE_CAST

  # Tally waits for all votes (triggered 3 times, runs when all present)
  TallyVotes:
    node_type: router
    event_triggers: [VOTE_CAST]
    event_emissions:
      - signal_name: APPROVED
        condition: |
          {{ context.vote_1 is defined and context.vote_2 is defined and context.vote_3 is defined and
             ((context.vote_1 == 'approve') | int + (context.vote_2 == 'approve') | int + (context.vote_3 == 'approve') | int) >= 2 }}
      - signal_name: REJECTED
        condition: |
          {{ context.vote_1 is defined and context.vote_2 is defined and context.vote_3 is defined and
             ((context.vote_1 == 'approve') | int + (context.vote_2 == 'approve') | int + (context.vote_3 == 'approve') | int) < 2 }}
"""

# =============================================================================
# DETERMINISTIC VOTING: For testing without LLM
# =============================================================================

# Simpler version that uses context values directly (deterministic test)
deterministic_voting = """
voting_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VOTES_READY

  TallyVotes:
    node_type: router
    event_triggers: [VOTES_READY]
    event_emissions:
      - signal_name: APPROVED
        condition: |
          {{ (context.votes | selectattr('vote', 'equalto', 'approve') | list | length) >= 2 }}
      - signal_name: REJECTED
        condition: |
          {{ (context.votes | selectattr('vote', 'equalto', 'approve') | list | length) < 2 }}

  HandleApproved:
    node_type: router
    event_triggers: [APPROVED]
    event_emissions:
      - signal_name: DONE

  HandleRejected:
    node_type: router
    event_triggers: [REJECTED]
    event_emissions:
      - signal_name: DONE
"""

# =============================================================================
# SIMPLE CONSENSUS: Majority wins
# =============================================================================

# Even simpler: count approvals in a list
simple_consensus = """
consensus_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHECK_CONSENSUS

  CheckConsensus:
    node_type: router
    event_triggers: [CHECK_CONSENSUS]
    event_emissions:
      - signal_name: CONSENSUS_REACHED
        condition: "{{ context.approve_count >= context.threshold }}"
      - signal_name: CONSENSUS_FAILED
        condition: "{{ context.approve_count < context.threshold }}"
"""
