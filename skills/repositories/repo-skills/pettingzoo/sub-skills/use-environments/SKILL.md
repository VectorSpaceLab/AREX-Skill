---
name: use-environments
description: "Use PettingZoo AEC and Parallel environments safely, including
  reset/step loops, action masks, rendering, seeding, and smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Use Environments

Use this sub-skill when an agent needs to instantiate a PettingZoo environment, write a bounded random or policy rollout, choose between AEC and Parallel loops, handle action masks, diagnose `step(None)`, run headless smoke checks, or reason about reset/step/render/close lifecycle.

## Read Or Run

- Read [references/aec-parallel-workflows.md](references/aec-parallel-workflows.md) when you need correct AEC and Parallel loop templates, return-value contracts, seeding notes, and validation tips.
- Read [references/action-masking-and-rendering.md](references/action-masking-and-rendering.md) when you need to locate action masks, sample masked actions, choose render modes, or handle dead-agent `None` actions.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a rollout fails with reset-order, optional dependency, mask, termination/truncation, GUI, or cleanup issues.
- Run [scripts/smoke_env_loop.py](scripts/smoke_env_loop.py) when you need a bounded CLI smoke check for a specific installed PettingZoo module and factory.

## Route Elsewhere

- For optional environment family extras, missing family dependencies, ROMs, or family selection, use [../environment-families/SKILL.md](../environment-families/SKILL.md).
- For wrappers, AEC/Parallel conversions, `AgentSelector`, `average_total_reward`, or `save_observation`, use [../wrappers-and-utilities/SKILL.md](../wrappers-and-utilities/SKILL.md).
- For implementing a new PettingZoo environment, use [../custom-environments/SKILL.md](../custom-environments/SKILL.md).
- For framework training recipes, vectorization, or long-running learning jobs, use [../training-integrations/SKILL.md](../training-integrations/SKILL.md).

## Default Stance

Prefer headless, bounded rollouts first: construct the environment with no GUI render mode, call `reset(seed=...)`, step only live agents, keep a hard step budget, and always call `close()` in `finally`.
