# SOE Advanced Patterns: Swarm Intelligence

## Introduction

Most agent frameworks rely on **conversation** (text back-and-forth). SOE relies on **signals**. This is much more efficient for coordinating multiple agents.

Swarm patterns enable:
- **Voting/Consensus** — Multiple agents vote, deterministic logic tallies
- **Jury Systems** — Parallel analysis with majority decision
- **Bidding/Auctions** — Agents compete via signal-based mechanisms

**Note**: Many swarm patterns leverage the **accumulated context** feature. For simpler fan-out and aggregation patterns, see [Fan-Out, Fan-In & Aggregations](guide_fanout_and_aggregations.md).

---

## Pattern 1: Simple Consensus

Check if a threshold is met using deterministic routing.

### The Workflow

```yaml
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
        condition: "&#123;&#123; context.approve_count >= context.threshold &#125;&#125;"
      - signal_name: CONSENSUS_FAILED
        condition: "&#123;&#123; context.approve_count < context.threshold &#125;&#125;"
```

### How It Works

1. Context contains `approve_count` and `threshold`
2. Router emits `CONSENSUS_REACHED` if threshold met
3. Router emits `CONSENSUS_FAILED` otherwise

**No LLM needed** — pure conditional logic handles the decision.

### Usage

```python
execution_id = orchestrate(
    config=simple_consensus,
    initial_workflow_name="consensus_workflow",
    initial_signals=["START"],
    initial_context={
        "approve_count": 5,
        "threshold": 3,
    },
    ...
)
# Result: CONSENSUS_REACHED signal emitted
```

---

## Pattern 2: Multi-Voter Tallying

Multiple voters provide input, router tallies the results.

### The Workflow

```yaml
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
          &#123;&#123; (context.votes | selectattr('vote', 'equalto', 'approve') | list | length) >= 2 &#125;&#125;
      - signal_name: REJECTED
        condition: |
          &#123;&#123; (context.votes | selectattr('vote', 'equalto', 'approve') | list | length) < 2 &#125;&#125;

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
```

### How It Works

1. Context contains a list of votes: `[{voter: "A", vote: "approve"}, ...]`
2. Router uses Jinja2 to count approvals
3. Emits `APPROVED` if majority approve, `REJECTED` otherwise

### The Jinja2 Magic

The condition uses Jinja2 filters to count:

```jinja
{{ (context.votes | selectattr('vote', 'equalto', 'approve') | list | length) >= 2 }}
```

This:
1. Filters votes where `vote == 'approve'`
2. Counts them
3. Compares to threshold

---

## Pattern 3: LLM-Based Voting (Full Swarm)

For real swarm intelligence, multiple LLM nodes can vote in parallel.

### The Workflow

```yaml
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
      Analyze if this content is appropriate: &#123;&#123; context.content &#125;&#125;
      You must output either "approve" or "reject".
    output_field: vote_1
    event_emissions:
      - signal_name: VOTE_CAST

  Voter2:
    node_type: llm
    event_triggers: [ANALYZE]
    prompt: |
      Analyze if this content is appropriate: &#123;&#123; context.content &#125;&#125;
      You must output either "approve" or "reject".
    output_field: vote_2
    event_emissions:
      - signal_name: VOTE_CAST

  Voter3:
    node_type: llm
    event_triggers: [ANALYZE]
    prompt: |
      Analyze if this content is appropriate: &#123;&#123; context.content &#125;&#125;
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
          &#123;&#123; context.vote_1 is defined and context.vote_2 is defined and context.vote_3 is defined and
             ((context.vote_1 == 'approve') | int + (context.vote_2 == 'approve') | int + (context.vote_3 == 'approve') | int) >= 2 &#125;&#125;
      - signal_name: REJECTED
        condition: |
          &#123;&#123; context.vote_1 is defined and context.vote_2 is defined and context.vote_3 is defined and
             ((context.vote_1 == 'approve') | int + (context.vote_2 == 'approve') | int + (context.vote_3 == 'approve') | int) < 2 &#125;&#125;
```

### How It Works

1. `ANALYZE` signal triggers all three voters **in parallel**
2. Each voter outputs to their own field (`vote_1`, `vote_2`, `vote_3`)
3. Each voter emits `VOTE_CAST`
4. `TallyVotes` router triggers on each `VOTE_CAST`
5. When all votes present, router emits final decision

**Key Insight**: The router runs multiple times but only emits the final signal when all votes are available (Jinja2 conditions check for all fields).

---

## Why Signals Beat Conversation

| Approach | Coordination Cost | Speed |
|----------|-------------------|-------|
| Conversation | Parse N paragraphs per round | Slow |
| Signals | Count N signal emissions | Fast |

For 12 agents voting, conversation requires parsing 12 text responses. Signals require counting 12 emissions. The signal approach scales to hundreds of agents.

---

## Related Patterns

- [Hybrid Intelligence](hybrid_intelligence.md) — Mix deterministic and AI logic
- [Self-Evolving Workflows](self_evolving_workflows.md) — Agents that modify their own workflows
