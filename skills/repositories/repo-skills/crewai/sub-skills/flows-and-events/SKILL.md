---
name: flows-and-events
description: "Use when building or debugging CrewAI Flow graphs, stateful flow
  execution, decorators, routers, persistence, checkpointing, plotting, human
  feedback, event listeners, and method hook ordering."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CrewAI Flows and Events

Use this sub-skill when the task is about CrewAI `Flow` classes, `@start`, `@listen`, `@router`, `and_`/`or_` triggers, state, routing labels, event ordering, flow plotting, replay/resume, or human feedback inside flows.

## Route by Intent

- Need exact decorator signatures, import paths, constructor options, or event types? Read [API reference](references/api-reference.md).
- Need flow graph design patterns, typed state, multiple starts, routers, persistence, checkpointing, plotting, conversational flows, or human feedback loops? Read [Flow patterns](references/flow-patterns.md).
- Need event listeners, event bus usage, flow method event ordering, scoped handlers, or before/after kickoff adjacency? Read [Event hooks](references/event-hooks.md).
- Need to diagnose missing listeners, router labels, state errors, plotting failures, duplicate resumed calls, or HITL loops? Read [Troubleshooting](references/troubleshooting.md).
- Need a safe static graph check for a user-defined flow class? Run [validate_flow_graph.py](scripts/validate_flow_graph.py) with `--help` first.

## Boundaries

- For `Agent`, `Task`, `Crew`, `Process`, guardrails, crew callbacks, or task-level human input, use [core-runtime](../core-runtime/SKILL.md).
- For `crewai create flow`, `crewai flow kickoff`, `crewai flow plot`, `crewai run`, or project scaffolds, use [cli-and-projects](../cli-and-projects/SKILL.md).
- For tracing/export provider setup, telemetry integrations, LLM hooks, tool hooks, or observability destinations, use [observability-and-hooks](../observability-and-hooks/SKILL.md).
- For root routing context across CrewAI packages, return to the [CrewAI root skill](../../SKILL.md).

## Safe Defaults

- Prefer static graph inspection and `flow.plot(...)` before running a flow with live LLMs or tools.
- Do not call `kickoff()` while only validating graph shape; `kickoff()` can execute user code, crews, tools, LLMs, and human prompts.
- Use explicit router `emit=[...]` or `Literal[...]` return annotations so static tools and plots can show intended route labels.
- Keep flow method names and route label strings stable; listeners depend on exact method names or exact emitted labels.
