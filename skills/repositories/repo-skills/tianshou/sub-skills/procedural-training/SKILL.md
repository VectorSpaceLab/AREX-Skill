---
name: procedural-training
description: "Wire Tianshou 2.0.1 procedural training pipelines with explicit
  environments, networks, policies, algorithms, collectors, and trainer params."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Procedural Training

Use this sub-skill when a user asks for manual Tianshou object wiring, low-level algorithm research, custom policies/algorithms, or phrases such as "procedural API", "manual DQN/PPO/SAC", "build policy/net/trainer", `OffPolicyTrainerParams`, or `DiscreteQLearningPolicy`.

## Use This For

- Building explicit Tianshou 2.0.1 pipelines from Gymnasium environments, networks, policies, algorithm objects, collectors, replay buffers, and trainer params.
- Selecting procedural algorithm families such as DQN variants, PPO, SAC, DDPG, TD3, TRPO, A2C, NPG, and Reinforce.
- Writing custom `Policy` or `Algorithm` subclasses and checking forward/update contracts before training.
- Diagnosing wiring errors around action spaces, action scaling, optimizers, trainer counts, and NaN/loss failures.

## Route Elsewhere

- Prefer `../highlevel-experiments/SKILL.md` for declarative experiment builders, high-level configs, persistence-first workflows, and quick benchmark-style experiments.
- Use `../data-collection/SKILL.md` for replay buffer internals, collector hooks, custom `Batch`/buffer flows, vector buffer tuning, and dataset collection details.
- Use `../offline-and-specialized-rl/SKILL.md` for offline RL, imitation learning, model-based RL, multi-agent RL, or domain-specific specializations.

## Fast Start

1. Confirm `tianshou` imports and that optional environment dependencies are installed only for the requested task family.
2. Create one probe environment and vectorized train/test environments, usually `DummyVectorEnv` for local CPU smoke tests.
3. Extract observation/action metadata with `SpaceInfo.from_env(env)` or the Gymnasium spaces directly.
4. Build network modules (`Net`, discrete/continuous actors, critics) that match the observation and action spaces.
5. Build a policy, then wrap it in the matching algorithm object with `AdamOptimizerFactory` or another optimizer factory.
6. Build collectors with a replay buffer for off-policy algorithms or a rollout buffer sized for on-policy collection.
7. Pass `OffPolicyTrainerParams`, `OnPolicyTrainerParams`, or `OfflineTrainerParams` to `algorithm.run_training(...)` only after a construction smoke passes.

## References

- `references/workflows.md` gives object construction order, on-policy/off-policy loops, custom extension points, trainer params, and validation checks.
- `references/api-reference.md` summarizes the procedural classes, current signatures, network helpers, and algorithm family map.
- `references/troubleshooting.md` covers action-space mismatches, action scaling, optimizer/model wiring, trainer count settings, NaNs, optional dependencies, and CLI/API misuse.
- `scripts/check_procedural_dqn_components.py` constructs tiny CartPole DQN components, runs a one-step collector smoke, and performs a policy forward pass without long training.

## Guardrails

- Keep procedural examples bounded until object wiring, action shapes, and collector counts are proven.
- Do not require the original Tianshou repository checkout at runtime; bundled scripts use installed public packages only.
- Avoid MuJoCo, Atari, Box2D, VizDoom, EnvPool, Ray, or robotics imports unless the user explicitly installed and requested those extras.
- For dict observations and action masks, preserve the nested observation contract expected by `DiscreteQLearningPolicy.forward`: `batch.obs` may contain the original observation plus `mask`.
