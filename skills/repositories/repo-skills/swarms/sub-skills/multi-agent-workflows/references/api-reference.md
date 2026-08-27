# Multi-agent API reference

## Constructor snapshot

This is a condensed reference for the most common swarm classes. Use the workflow guide for full examples.

| Class | Verified key knobs | Typical output |
| --- | --- | --- |
| `SequentialWorkflow` | `agents`, `max_loops`, `output_type`, `autosave`, `team_awareness`, `drift_detection`, `drift_threshold`, `drift_model`, `drift_max_retries` | ordered transcript / formatted history |
| `ConcurrentWorkflow` | `agents`, `show_dashboard`, `on_error`, `max_workers`, `output_type`, `autosave` | concurrent results collected together |
| `AgentRearrange` | `agents`, `flow`, `max_loops`, `output_type`, `team_awareness`, `autosave` | flow-driven transcript / formatted output |
| `GraphWorkflow` | `add_node`, `add_edge`, `set_entry_points`, `set_end_points`, `run` | DAG execution result mapping |
| `SwarmRouter` | `swarm_type`, `rearrange_flow`, `multi_agent_collab_prompt`, `heavy_swarm_variant`, `heavy_swarm_max_loops`, `director_model_name`, `council_judge_model_name` | selected swarm output |
| `MixtureOfAgents` | `agents`, `aggregator_agent`, `layers`, `output_type`, `max_workers` | synthesized response |
| `HierarchicalSwarm` | `director`, `agents`, `max_loops`, `output_type` | director/worker synthesis |
| `GroupChat` | `agents`, `threshold`, `recency_penalty`, `recency_window`, `max_loops` | turn-based conversation transcript |
| `MajorityVoting` | `agents`, `consensus_agent_prompt`, `consensus_agent_model_name`, `max_loops`, `output_type` | consensus result |
| `CouncilAsAJudge` | `agents`, `judge`, `max_loops`, `output_type` | judge verdict |
| `DebateWithJudge` | `agents`, `judge`, `max_loops`, `output_type` | debate transcript + verdict |
| `RoundRobinSwarm` | `agents`, `max_loops`, `output_type` | turn-by-turn conversation |
| `PlannerWorkerSwarm` | `agents`, `max_loops`, task queue / worker pool helpers | planned task execution |
| `HeavySwarm` | `variant`, `question_agent_model_name`, `worker_model_name`, `show_dashboard`, `timeout`, `max_loops` | decomposed analysis + synthesis |
| `BatchedGridWorkflow` | `agents`, `max_loops`, `output_type` | batch grid results |
| `MultiAgentRouter` | `agents`, `model`, `temperature`, `skip_null_tasks`, `output_type` | routed handoff result |

## `SwarmType`

Verified choices in the router include:

- `SequentialWorkflow`
- `ConcurrentWorkflow`
- `AgentRearrange`
- `MixtureOfAgents`
- `HierarchicalSwarm`
- `GroupChat`
- `MultiAgentRouter`
- `MajorityVoting`
- `CouncilAsAJudge`
- `DebateWithJudge`
- `HeavySwarm`
- `BatchedGridWorkflow`
- `RoundRobin`
- `PlannerWorkerSwarm`
- `LLMCouncil`
- `auto`

## Flow syntax

`AgentRearrange` uses a simple DSL:

- `A -> B` means sequential execution.
- `A, B` means concurrent execution.
- `A -> B, C -> D` combines both.

The flow must reference registered agent names.

## Key behavior notes

- `ConcurrentWorkflow` is network-bound in real use, so the thread pool is sized around agent count rather than CPU count.
- `GraphWorkflow` supports optional graph backends and can fall back when `graphviz` or `rustworkx` is missing.
- `GroupChat` requires each agent to carry `RESPOND_TOOL` so the chat can ask whether to speak.
- `SwarmRouter` is a router/factory, not just a pass-through; it may create a concrete swarm based on `swarm_type`.

## Practical selection guide

- Use `SequentialWorkflow` when every step depends on the previous one.
- Use `ConcurrentWorkflow` when the same task can be solved independently by many agents.
- Use `AgentRearrange` when you want explicit `->` and `,` routing.
- Use `GraphWorkflow` when the dependency graph is non-linear or fan-out/fan-in is central.
- Use `SwarmRouter` when you want one entry point that can pick the swarm type later.
