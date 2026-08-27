---
name: composer-environments
description: "Create and validate custom dm_control Composer entities, tasks,
  observables, variations, and Environment loops."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# composer-environments

Use this sub-skill when a task needs a custom `dm_control.composer` environment: new `Entity` subclasses, a `Task` with lifecycle hooks and rewards, entity or task observables, per-episode randomization, or a `composer.Environment` reset/step loop.

Do not use this sub-skill for ready-made locomotion, manipulation, or soccer task catalogs; route those to [`../locomotion-manipulation/SKILL.md`](../locomotion-manipulation/SKILL.md). Route raw MJCF parsing/exporting/model surgery to [`../mjcf-mujoco-models/SKILL.md`](../mjcf-mujoco-models/SKILL.md), and Control Suite benchmark loading/wrappers to [`../suite-rl-workflows/SKILL.md`](../suite-rl-workflows/SKILL.md). If a custom observable renders camera pixels and the error is OpenGL/backend-specific, use [`../rendering-viewer-assets/SKILL.md`](../rendering-viewer-assets/SKILL.md) for backend selection.

## Prerequisites and safe default

Use an installed `dm_control` package. Public install commands only:

```bash
python -m pip install dm_control
# For unreleased source snapshots only:
python -m pip install git+https://github.com/google-deepmind/dm_control.git
```

Do not use editable installs; dm_control does not support editable mode. Composer model construction and non-rendering reset/step loops are CPU workflows. Camera observables are rendering workflows and need a separately validated OpenGL backend.

## First decisions

1. **Entity structure:** implement `composer.Entity._build(...)`, store a `mjcf.RootElement` or attached model, return it from `mjcf_model`, and return a `composer.Observables` subclass from `_build_observables()` when the entity exposes observations.
2. **Task contract:** implement `root_entity`, `get_reward(physics)`, optional `task_observables`, optional termination/discount/spec methods, and lifecycle hooks only where needed.
3. **Timing:** set `physics_timestep` and `control_timestep` through `Task.set_timesteps(...)` or the task properties. Ensure the control timestep is an integer multiple of the physics timestep.
4. **Environment options:** choose `random_state`, `time_limit`, `max_reset_attempts`, recompilation behavior, observation buffer shape options, and physics error policy before training.
5. **Validation before training:** instantiate the task, create `composer.Environment`, run `reset()` and several `step(action)` calls with actions from `action_spec()`, verify observation keys/shapes against `observation_spec()`, confirm reward/discount/termination behavior, and exercise any stochastic episode initialization with fixed seeds.

## Bundled operating files

- Read [`references/composer-api-reference.md`](references/composer-api-reference.md) when implementing Composer class contracts, lifecycle hooks, environment options, observable key qualification, random-state handling, or recompilation behavior.
- Read [`references/observables-and-variation.md`](references/observables-and-variation.md) when configuring enabled observables, buffers, delays, aggregators, corruptors, `@composer.observable`, or variation/distribution/noise randomizers.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when abstract method errors, missing `mjcf_model`/`root_entity`, bad observable keys, dead physics proxies, reset retry failures, or action-shape mismatches appear.
- Run [`scripts/composer_minimal_task.py`](scripts/composer_minimal_task.py) to smoke-test an installed-package Composer entity/task/environment loop and inspect action specs, observation specs, fully qualified keys, hook counts, and short rollout behavior.

## Minimal validation command

From this sub-skill directory:

```bash
python scripts/composer_minimal_task.py --steps 5 --seed 7
```

Expected signal: the script prints one bounded action spec, observation specs containing a task-level key and entity-qualified keys, a `control_timestep`, a `physics_steps_per_control_step`, several successful `step` lines, and hook counts consistent with the configured number of physics substeps. If this smoke fails, fix import/install or core Composer construction before using the custom environment for training.
