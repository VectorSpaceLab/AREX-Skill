---
name: env-integration
description: "Routes DI-engine environment wrappers, env managers, and DIZoo
  environment onboarding."
metadata:
  disco-role: operating
  disable-model-invocation: true
license: Apache 2.0
disable-model-invocation: true
---

# Environment integration

Use this sub-skill for environment wrappers, env-manager selection, and the
DIZoo patterns used to add or debug a new environment.
The key question is usually "what shape should the environment return, and how
should DI-engine manage it?"

## Owns

- `DingEnvWrapper` and its collector/evaluator configuration helpers
- `BaseEnvManager`, `BaseEnvManagerV2`, `EnvSupervisor`, and subprocess-based
  env management
- `create_env_manager`, `get_vec_env_setting`, and related env-manager helpers
- environment-template patterns under `dizoo/classic_control/`, `bitflip/`,
  `frozen_lake/`, and `league_demo/`
- env-shape debugging for observation, action, reward, and done semantics

## Does not own

- Legacy training loops and data collection logic; those belong to
  `serial-pipelines`
- Framework/middleware examples and multi-process message routing; those belong
  to `framework-runtime`
- CLI flag parsing and config compilation; those belong to `cli-config`

## Read this first when the user asks

- how to wrap a Gym or Gymnasium environment for DI-engine
- how to choose the right env manager backend
- how to add a new environment under `dizoo/`
- why a collector or evaluator env is returning the wrong shapes
- why a manager is timing out, blocking, or restarting children

## Workflow

1. Use `references/environment-reference.md` to identify the wrapper or manager
   the request needs.
2. Use `references/troubleshooting.md` when the user sees shape or timeout
   errors.
3. Use `scripts/env_wrapper_smoke.py` for a small check that the installed
   environment can still wrap and step a representative env.
4. If the problem is really about policy or pipeline logic, move to the
   neighboring sub-skill instead of widening this one.

## Common decision points

- Use `DingEnvWrapper` when you need to normalize a Gym/Gymnasium env into the
  DI-engine timestep and action/observation conventions.
- Use `BaseEnvManager` or `BaseEnvManagerV2` for local single-machine env
  management.
- Use `EnvSupervisor` when the workflow needs explicit child restart and
  timeout control.
- Use the `dizoo/classic_control/` family as the simplest representative
  environment pattern when you are onboarding a new env.

## Helpful bundle links

- `references/environment-reference.md` for signatures, manager choices, and
  representative environment families.
- `references/troubleshooting.md` for shape, timeout, and optional-package
  failures.
- `scripts/env_wrapper_smoke.py` for a small wrapper check using CartPole under
  both Gym and Gymnasium.
