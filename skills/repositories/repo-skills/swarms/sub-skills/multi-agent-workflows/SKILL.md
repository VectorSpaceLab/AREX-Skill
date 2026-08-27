---
name: multi-agent-workflows
description: "Guide Swarms orchestration, routing, debate, consensus, and
  graph-based multi-agent workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Multi-agent workflows

Use this sub-skill when the user wants to combine multiple agents into a swarm, route tasks between agents, or choose an orchestration pattern.

## Owns these workflows

- Linear and concurrent pipelines: `SequentialWorkflow`, `ConcurrentWorkflow`.
- DSL and graph orchestration: `AgentRearrange`, `GraphWorkflow`.
- Routing and selection: `SwarmRouter`, `MultiAgentRouter`.
- Collaboration and consensus: `MixtureOfAgents`, `HierarchicalSwarm`, `GroupChat`, `MajorityVoting`, `CouncilAsAJudge`, `DebateWithJudge`.
- Other swarm styles: `RoundRobinSwarm`, `PlannerWorkerSwarm`, `HeavySwarm`, `BatchedGridWorkflow`.

## Does not own

- One-agent configuration and runtime behavior; use `single-agent`.
- CLI and file-driven creation flows; use `cli-loaders`.
- Tool schema conversion and MCP transport; use `tools-mcp`.

## Read this sub-skill when the request mentions

- `SequentialWorkflow`, `ConcurrentWorkflow`, `AgentRearrange`, `GraphWorkflow`, or `SwarmRouter`.
- `MixtureOfAgents`, `HierarchicalSwarm`, `GroupChat`, `MajorityVoting`, `CouncilAsAJudge`, or `DebateWithJudge`.
- `RoundRobinSwarm`, `PlannerWorkerSwarm`, `HeavySwarm`, `BatchedGridWorkflow`, or `MultiAgentRouter`.
- `RESPOND_TOOL`, fan-out/fan-in, DAGs, consensus, routing, or collaborator selection.

## Working shape

1. Identify the exact orchestration style the user wants.
2. Decide whether the task is a simple chain, a fan-out/fan-in graph, a consensus loop, or an automatic router selection problem.
3. Check whether the workflow needs fake agents, real provider-backed agents, or optional graph backends.
4. Use the bundled references for class selection, flow syntax, and failure handling.

## What to read next

- `references/workflows.md` for the orchestration catalog and route-selection guidance.
- `references/api-reference.md` for constructor and method summaries.
- `references/troubleshooting.md` for flow, backend, and concurrency issues.
- `scripts/workflow_smoke.py` for an offline workflow smoke check with fake agents.

## Typical user questions this sub-skill should answer

- Which swarm class should I use for sequential vs parallel processing?
- How do I express a mixed `->` and `,` flow in `AgentRearrange`?
- When should I use `SwarmRouter` instead of directly constructing a swarm?
- Why does `GroupChat` need `RESPOND_TOOL` on each agent?
- How do I debug a swarm that returns the wrong type or never converges?

## Route boundaries

- If the task is only about one agent, route to `single-agent`.
- If the task starts from a CLI or config file, route to `cli-loaders`.
- If the task is about tools, BaseTool, or MCP, route to `tools-mcp`.

## Acceptance checklist

- The response should name the exact swarm class and why it fits the task.
- The response should describe the input shape and expected output shape.
- The response should mention optional dependencies such as graph backends when relevant.
- The response should include at least one concrete troubleshooting path for empty agents, invalid flows, or provider/backend issues.
