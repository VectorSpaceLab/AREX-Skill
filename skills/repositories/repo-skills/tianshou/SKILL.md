---
name: tianshou
description: "Use Tianshou 2.0.1 for PyTorch/Gymnasium deep reinforcement
  learning experiments, custom procedural training, data collection, vectorized
  environments, offline RL, multi-agent RL, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tianshou

Use this repo skill when a user asks for Tianshou, `tianshou`, PyTorch + Gymnasium reinforcement learning, high-level `ExperimentBuilder` workflows, procedural policy/algorithm/trainer wiring, replay buffers and collectors, vectorized environments, offline RL, imitation learning, model-based/curiosity wrappers, multi-agent RL, or Tianshou evaluation helpers.

## Start Here

1. Confirm `tianshou` imports and the requested environment/backend extras are installed.
2. Choose the narrowest sub-skill route below before writing code.
3. Keep first runs bounded: CPU, `DummyVectorEnv`, tiny step counts, no rendering, no downloads, and no benchmark-scale training unless the user explicitly asks.
4. Use the bundled scripts for safe import/construction smokes before long training or optional backend work.
5. If a task spans routes, use the primary workflow sub-skill first and cross-link for buffers, envs, or evaluation details.

## Route Map

- Use `sub-skills/highlevel-experiments/SKILL.md` for declarative builder workflows: `ExperimentBuilder`, `DQNExperimentBuilder`, `PPOExperimentBuilder`, `ExperimentConfig`, training configs, algorithm params dataclasses, persistence/watch/logging, and quick applied-RL skeletons.
- Use `sub-skills/procedural-training/SKILL.md` for manual low-level wiring: Gymnasium envs, networks, policies, algorithms, optimizer factories, collectors, replay buffers, `OffPolicyTrainerParams`, `OnPolicyTrainerParams`, and custom algorithm or policy research.
- Use `sub-skills/data-collection/SKILL.md` for `Batch`, `ReplayBuffer`, `VectorReplayBuffer`, prioritized/HER buffers, `Collector`, `AsyncCollector`, hooks, n-step/return data, stats, shape issues, and malformed buffer debugging.
- Use `sub-skills/envs-and-vectorization/SKILL.md` for Gymnasium/PettingZoo wrappers, `DummyVectorEnv`, `SubprocVectorEnv`, `RayVectorEnv`, EnvPool-style integration, action masks, seeding/reset/close behavior, and optional engines such as Atari, Box2D, MuJoCo, VizDoom, robotics, or Ray.
- Use `sub-skills/offline-and-specialized-rl/SKILL.md` for CQL/BCQ/TD3+BC, imitation/GAIL, PSRL, ICM wrappers, multi-agent algorithm wrappers, `JoblibExpLauncher`, rliable evaluation, and benchmark planning.

## Common Route Signals

| User asks about | Route |
| --- | --- |
| "quick DQN CartPole with Tianshou", "builder", "high-level API" | `sub-skills/highlevel-experiments/SKILL.md` |
| "custom policy", "manual PPO/SAC", "trainer params", "network wiring" | `sub-skills/procedural-training/SKILL.md` |
| "Batch slicing", "ReplayBuffer sample", "Collector.collect", "n-step returns" | `sub-skills/data-collection/SKILL.md` |
| "SubprocVectorEnv", "PettingZooEnv", "action mask", "MuJoCo install", "EnvPool" | `sub-skills/envs-and-vectorization/SKILL.md` |
| "offline dataset", "CQL", "GAIL", "PSRL", "multi-agent", "rliable" | `sub-skills/offline-and-specialized-rl/SKILL.md` |

## Cross-Cutting References

- `references/installation-and-routing.md` summarizes package setup, optional extras, API-level choice, and smoke commands.
- `references/troubleshooting.md` covers install/import, optional dependency, data/config, CLI/API misuse, and workflow failure patterns shared across sub-skills.
- `references/evaluation-and-benchmarks.md` explains safe evaluation, multi-seed launchers, rliable outputs, and benchmark-scale guardrails.
- `references/repo-provenance.md` records the source commit, version, dirty state, and evidence paths used to generate this skill.
- `references/repo-routing-metadata.json` is structured metadata consumed by DisCo's `repo-skills-router` import.
- `scripts/check_tianshou_install.py` performs a safe import/API smoke for installed Tianshou without training, downloads, or source checkout reads.

## Safe Smoke Commands

```bash
python skills/tianshou/scripts/check_tianshou_install.py
python skills/tianshou/sub-skills/highlevel-experiments/scripts/check_highlevel_cartpole.py
python skills/tianshou/sub-skills/procedural-training/scripts/check_procedural_dqn_components.py
python skills/tianshou/sub-skills/data-collection/scripts/check_batch_buffer_collector.py
python skills/tianshou/sub-skills/envs-and-vectorization/scripts/check_vector_env.py --num-envs 2 --steps 4
python skills/tianshou/sub-skills/offline-and-specialized-rl/scripts/check_offline_api_imports.py --strict --no-include-optional
```

## Guardrails

- Do not run Atari, MuJoCo, Box2D, VizDoom, robotics, EnvPool, Ray, D4RL, benchmark, or multi-seed workflows until their optional dependencies and data/assets are explicitly available.
- Do not treat benchmark examples as smoke tests; reduce to imports, constructors, tiny envs, tiny buffers, or one-seed dry checks first.
- Do not use high-level builders when the user needs custom collector hooks, replay-buffer internals, custom training loops, or algorithm research; route to the procedural and data sub-skills.
- Keep generated code version-aware: Tianshou v2 separates `Algorithm` and `Policy`, uses builder/config dataclasses in the high-level API, and is not backwards-compatible with v1 parameter names.
