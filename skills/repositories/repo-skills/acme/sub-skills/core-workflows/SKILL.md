---
name: core-workflows
description: "Build and debug Acme core dm_env loops, specs, wrappers, logging,
  counting, observers, and simple custom Actor/Learner components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Acme Core Workflows

Use this sub-skill when an agent needs to assemble or debug the framework-level Acme loop before choosing a JAX, TensorFlow/Sonnet, or distributed backend.

## Read First

- Start with [Core API contracts](references/core-api.md) for exact signatures, method ordering, and import surfaces.
- Use [Core workflows](references/workflows.md) for adapting Gym-like environments, building a minimal `Actor`, wiring `EnvironmentLoop`, wrappers, loggers, counters, and observers.
- Use [Core troubleshooting](references/troubleshooting.md) when loop bounds, specs, dtypes, wrapper behavior, logger timing, or optional backend imports fail.
- Run [check_core_imports.py](scripts/check_core_imports.py) to inspect the local Acme installation without requiring JAX/TF/Reverb/Launchpad execution.

## Scope

This sub-skill covers:

- `acme.core.Actor`, `Learner`, `VariableSource`, `Saveable`, and `Worker` component contracts.
- `acme.specs` aliases and `make_environment_spec(environment)` for `dm_env` environments.
- `acme.EnvironmentLoop` and `acme.environment_loop.EnvironmentLoop` single-environment interaction.
- Core wrappers from `acme.wrappers`, especially `GymWrapper`, `SinglePrecisionWrapper`, `CanonicalSpecWrapper`, `EnvironmentWrapper`, and `wrap_all`.
- `acme.utils.counting.Counter`, `acme.utils.loggers`, `acme.utils.observers`, and signal-safe loop termination basics.

Route elsewhere:

- Replay adders, Reverb tables, datasets, and iterator pipelines belong in `replay-and-data`.
- JAX networks, builders, experiments, and agent-specific JAX behavior belong in `jax-agents`.
- TensorFlow/Sonnet agents and Launchpad-backed TF examples belong in `tf-agents`.

## Quick Routing

- If the user has a custom environment, first make it implement `dm_env.Environment` or wrap it with `acme.wrappers.GymWrapper`, then verify `observation_spec()`, `action_spec()`, `reward_spec()`, and `discount_spec()`.
- If the user has a loop failure, check `EnvironmentLoop.run()` bounds, action/spec dtype compatibility, and whether optional imports are failing before the loop starts.
- If the user needs metrics, prefer `Counter`, a `Logger` implementation, and `EnvLoopObserver` instances instead of modifying `EnvironmentLoop` internals.
- If the user asks for a complete learning agent, keep this sub-skill focused on the `Actor`/`Learner` interface and route backend-specific network or replay decisions to the backend/data sub-skills.
