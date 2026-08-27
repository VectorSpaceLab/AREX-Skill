# Multi-agent workflow guide

## Choose the right orchestration style

| Situation | Good fit |
| --- | --- |
| One step after another | `SequentialWorkflow` |
| Same prompt to many agents at once | `ConcurrentWorkflow` |
| Explicit mixed sequential and parallel routing | `AgentRearrange` |
| DAG with named dependencies | `GraphWorkflow` |
| One entry point that chooses a swarm later | `SwarmRouter` |
| Many independent opinions, then synthesize | `MixtureOfAgents` |
| Director plus workers | `HierarchicalSwarm` |
| Turn-based discussion | `GroupChat` or `RoundRobinSwarm` |
| Majority/consensus decision | `MajorityVoting` or `CouncilAsAJudge` |
| Adversarial argument with final verdict | `DebateWithJudge` |
| Large decomposed analysis | `HeavySwarm` |
| Task queue and worker loop | `PlannerWorkerSwarm` |
| Grid/batch execution | `BatchedGridWorkflow` |
| Best-fit routing to one or more agents | `MultiAgentRouter` |

## Linear pipeline

Use `SequentialWorkflow` when the output of one agent should become the next agent’s input.

## Concurrent pipeline

Use `ConcurrentWorkflow` when each agent can work independently on the same task.

- Keep `agents` non-empty.
- Use `show_dashboard=True` only when you want the richer progress view.
- For real runs, remember that the underlying work is usually network-bound.

## Flow DSL

Use `AgentRearrange` when you want the execution order to be visible in a single string.

Example:

```text
Research -> Writer, Reviewer -> Publisher
```

The main thing to check is whether every name in the flow matches a real agent.

## Graph workflows

Use `GraphWorkflow` when the execution pattern is easier to reason about as a DAG than as a text flow.

- Add nodes first.
- Add edges next.
- Set entry and end points.
- Check optional backend availability only if you actually need the visualization or backend-specific path.

## Router workflows

Use `SwarmRouter` when you want a single object that can select among multiple swarm styles.

- It is good for applications that need a stable entry point.
- It is also useful when you want the swarm type to remain configurable.
- If the task needs a specific flow string, provide `rearrange_flow` for `AgentRearrange` routes.

## Collaboration and consensus

- `MixtureOfAgents` is for parallel expert opinions plus synthesis.
- `HierarchicalSwarm` is for manager/director style delegation.
- `GroupChat` is for turn-taking discussion where each agent can decide whether to speak.
- `MajorityVoting` is for discrete decision support.
- `CouncilAsAJudge` and `DebateWithJudge` are for adjudicated reasoning.

## Offline smoke pattern

For local validation, prefer fake agents with a simple `run()` method. That lets you test flow syntax, routing, and output formatting without making a live model call.
