---
name: suite-rl-workflows
description: "Load, inspect, step, wrap, and validate dm_control suite environments."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# suite-rl-workflows

Use this skill when the request mentions Control Suite benchmark tasks, `suite.load`, `action_spec` / `observation_spec`, `dm_env.TimeStep`, random rollouts, flat observations, action scaling or noise wrappers, pixel observations, or reward visualization.

## Start here

- [Suite API reference](references/suite-api-reference.md) — read this for loader signatures, task collections, `TimeStep` basics, validation snippets, and the `task_kwargs` / `environment_kwargs` split.
- [Wrappers and observations](references/wrappers-and-observations.md) — read this when you need `action_scale`, `action_noise`, `pixels`, `mujoco_profiling`, flat-observation behavior, or reward-color cues.
- [Troubleshooting](references/troubleshooting.md) — read this when the load, rollout, render, or import path fails.
- [Random rollout script](scripts/suite_random_rollout.py) — run this for a safe installed-package smoke test that prints spec summaries and steps a built-in suite task.

## What this skill covers

- `dm_control.suite.load(...)` and `dm_control.suite.build_environment(...)`
- `suite.ALL_TASKS`, `suite.BENCHMARKING`, and `suite.TASKS_BY_DOMAIN`
- `dm_control.rl.control.Environment`, `Task`, `Physics`, and `flatten_observation`
- suite wrappers: `action_scale`, `action_noise`, `pixels`, and `mujoco_profiling`
- minimal non-rendering rollout loops and validation signals
- `visualize_reward` for rendered reward cues

## What to route elsewhere

- MJCF or MuJoCo model construction, parsing, export, or compile/step details: [mjcf-mujoco-models](../mjcf-mujoco-models/SKILL.md)
- Composer custom tasks, entities, observables, variation, or environment hooks: [composer-environments](../composer-environments/SKILL.md)
- Locomotion, soccer, walkers, mocap, or registry-style built-in environment catalogs: [locomotion-manipulation](../locomotion-manipulation/SKILL.md)
- Viewer launchers, render backend selection, or GUI/headless OpenGL operations: [rendering-viewer-assets](../rendering-viewer-assets/SKILL.md)

## Quick decision guide

1. Need a built-in Control Suite task? Use `suite.load(domain_name, task_name, ...)`.
2. Need to confirm names before loading? Check `suite.TASKS_BY_DOMAIN` or iterate `suite.ALL_TASKS`.
3. Need normalized actions? Use `action_scale`.
4. Need exploration noise? Use `action_noise`.
5. Need pixels? Use `pixels` and read the backend caveats first.
6. Need a flat state vector? Use `flat_observation=True` or `control.flatten_observation`.
7. Need step timing? Use `mujoco_profiling`.
8. Need registry-style built-in environments outside the Control Suite benchmark family? Route to [locomotion-manipulation](../locomotion-manipulation/SKILL.md).
