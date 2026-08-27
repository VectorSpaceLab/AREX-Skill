---
name: highlevel-experiments
description: "Use Tianshou 2.0.1 high-level experiment builders for declarative
  Gymnasium-style RL experiments with minimal boilerplate."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# High-Level Experiments

Use this sub-skill when a user asks for Tianshou's declarative high-level API, `ExperimentBuilder`, `DQNExperimentBuilder`, `PPOExperimentBuilder`, `SACExperimentBuilder`, algorithm params dataclasses, experiment configs, persistence/watch settings, or a quick builder-based experiment skeleton.

## Use This For

- Applying existing Tianshou algorithms to Gymnasium-style tasks with `EnvFactoryRegistered`, `ExperimentConfig`, and an on-policy or off-policy training config.
- Building `DQNExperimentBuilder`, `PPOExperimentBuilder`, `SACExperimentBuilder`, and related algorithm-specific builders with concise `with_*` chains.
- Disabling persistence, logs, watch/render, or GPU defaults for safe smoke tests and notebook/CI snippets.
- Translating simple procedural experiment requests into a high-level builder when no custom collector, policy, or trainer loop is required.

## Route Elsewhere

- Use `../procedural-training/SKILL.md` for manual network, policy, optimizer, collector, replay buffer, trainer, or custom algorithm wiring.
- Use `../data-collection/SKILL.md` for replay buffer mechanics, collector hooks, buffer sizing internals, and custom collection flows.
- Use `../envs-and-vectorization/SKILL.md` for optional environment engines, custom vectorization, EnvPool, Ray, Atari wrappers, MuJoCo/Box2D installs, or environment registration failures.

## Fast Start

1. Confirm the task id is available through Gymnasium and whether it has discrete or continuous actions.
2. Choose `EnvFactoryRegistered(task=..., venv_type=VectorEnvType.DUMMY)` for portable local smokes; use heavier vector types only when dependencies and multiprocessing constraints are known.
3. Set `ExperimentConfig(persistence_enabled=False, log_file_enabled=False, watch=False, device="cpu")` for safe construction and CI checks.
4. Pick `OffPolicyTrainingConfig` for DQN/SAC/DDPG/TD3/REDQ/IQN or `OnPolicyTrainingConfig` for PPO/A2C/TRPO/NPG/Reinforce.
5. Instantiate the algorithm builder, chain the matching params and default model/actor/critic factories, then call `.build()` for a construction check or `.run()` only for a deliberate training run.
6. Add `EpochStopCallbackRewardThreshold(...)` only when the experiment will actually train and test reward thresholds are meaningful.

## References

- `references/workflows.md` gives builder recipes, config decisions, persistence/watch/logging cautions, and high-level-to-procedural crossover guidance.
- `references/api-reference.md` summarizes current public high-level classes, builder methods, signatures, defaults, and algorithm-family mapping.
- `references/troubleshooting.md` covers API-v2 migration confusion, optional environment dependencies, persistence/logging directories, GPU defaults, parameter symptoms, and workflow failures.
- `scripts/check_highlevel_cartpole.py` imports high-level APIs and builds a bounded CartPole DQN experiment without long training, rendering, downloads, or source-checkout access.

## Guardrails

- Keep examples self-contained and runnable from an installed `tianshou` package; do not require the original repository checkout.
- Default new high-level smokes to CPU, `VectorEnvType.DUMMY`, `persistence_enabled=False`, and `watch=False` unless the user asks to train/watch/save.
- Do not use high-level builders when the user needs custom replay-buffer internals, collector hooks, or a custom training loop; route to the focused sibling sub-skill.
- Treat Atari, MuJoCo, Box2D, VizDoom, EnvPool, Ray, and robotics tasks as optional dependency areas that need explicit environment support before running.
