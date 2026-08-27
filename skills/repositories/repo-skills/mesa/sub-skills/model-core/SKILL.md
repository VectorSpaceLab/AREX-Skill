---
name: model-core
description: "Build and run Mesa core models with agents, activation, time
  advancement, lifecycle, and event scheduling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Core

Use this sub-skill when the task is about Mesa's core modeling layer: `Model`, `Agent`, `AgentSet`, `GroupBy`, automatic registration, activation patterns, reproducible RNG, lifecycle/removal, and event scheduling.

Start here:

- [API reference](references/api-reference.md) for verified signatures, object relationships, and gotchas.
- [Workflows](references/workflows.md) for copyable first-model, activation, event, lifecycle, and RNG recipes.
- [Troubleshooting](references/troubleshooting.md) for common failure modes and quick fixes.
- [Smoke script](scripts/mesa_model_smoke.py) for a safe runtime check against an installed Mesa package.

Do:

- Build agents with `mesa.Agent` and models with `mesa.Model`.
- Create agents with `Agent.create_agents` or `Agent.from_dataframe`.
- Activate agents with `model.agents.do(...)`, `shuffle_do(...)`, or `model.agents_by_type[...]`.
- Advance simulations with `run_for`, `run_until`, or `run_model`.
- Schedule one-off and recurring work with `schedule_event` and `schedule_recurring`.
- Remove agents with `agent.remove()` and clear a model with `remove_all_agents()`.
- Use `rng=` or a `Scenario` instance for reproducible randomness.

Route elsewhere when needed:

- Spatial placement and movement: [../spaces/SKILL.md](../spaces/SKILL.md)
- Data collection and scenario experiments: [../analysis-experiments/SKILL.md](../analysis-experiments/SKILL.md)
- Visualization dashboards: [../visualization/SKILL.md](../visualization/SKILL.md)

Keep this sub-skill focused on core model mechanics; do not fold in space, analysis, or visualization workflows here.
