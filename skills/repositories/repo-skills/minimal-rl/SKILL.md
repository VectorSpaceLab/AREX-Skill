---
name: minimal-rl
description: "Guides minimalRL single-file PyTorch reinforcement-learning
  algorithms, smoke checks, Gym compatibility, and adaptation routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# minimalRL

Use this repo skill when a task involves minimalRL's compact PyTorch reinforcement-learning examples: choosing an algorithm file, adapting a single-file implementation, checking tensor shapes, or troubleshooting Gym/PyTorch compatibility before running training.

## What this skill covers

minimalRL is an educational collection of self-contained PyTorch RL algorithms. The generated skill is self-contained: use the bundled references and smoke scripts here instead of relying on the original checkout at runtime.

Read [references/algorithm-catalog.md](references/algorithm-catalog.md) when you need a cross-algorithm table of environments, action spaces, classes, and owning sub-skills.

## Install and environment baseline

The selected runtime scope is CPU-first. GPU packages are not required for the repository's public examples.

Use a Python environment with:

```bash
python -m pip install "torch" "gym==0.26.2" "numpy<2"
```

Then run the shared smoke helper:

```bash
python scripts/check_minimal_rl_env.py --make-envs
```

Notes:

- The scripts use `import gym`, not `gymnasium`. Gym 0.26 emits a deprecation warning, but it matches the repository's dependency statement.
- Pin `numpy<2` with Gym 0.26 to avoid known compatibility problems.
- The repository is not a Python package with a stable import name; the original project is a set of top-level training scripts. This skill therefore bundles distilled references and standalone smoke helpers.

## Route by algorithm family

- **REINFORCE, vanilla actor-critic, discrete PPO, PPO-LSTM, or on-policy CartPole updates**: read [sub-skills/on-policy-discrete/SKILL.md](sub-skills/on-policy-discrete/SKILL.md).
- **DQN, ACER, replay buffers, target networks, or V-trace off-policy correction**: read [sub-skills/off-policy-value/SKILL.md](sub-skills/off-policy-value/SKILL.md).
- **DDPG, PPO-Continuous, SAC, Pendulum, continuous actions, OU noise, Gaussian policies, or soft target updates**: read [sub-skills/continuous-control/SKILL.md](sub-skills/continuous-control/SKILL.md).
- **A2C, A3C, multiprocessing, vectorized workers, shared global models, or Gym migration for parallel scripts**: read [sub-skills/parallel-actor-critic/SKILL.md](sub-skills/parallel-actor-critic/SKILL.md).

## Common operating flow

1. Identify the action type: discrete CartPole routes to `on-policy-discrete`, `off-policy-value`, or `parallel-actor-critic`; continuous Pendulum routes to `continuous-control`.
2. Read the sub-skill's API reference before editing network dimensions, replay tuple fields, action scaling, or training loops.
3. Run the nearest bundled smoke script before attempting full training. The original examples run many episodes; shape and data-contract checks are faster and safer.
4. If you are porting to a new Gym environment, update observation dimensions, action dimensions, reward scaling, and Gym reset/step handling together.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, Gym, NumPy, and PyTorch failures; use the sub-skill troubleshooting file for algorithm-specific symptoms.

## Shared bundled files

- [references/algorithm-catalog.md](references/algorithm-catalog.md) maps every covered algorithm to its environment, action type, core class/function surfaces, and owner.
- [references/troubleshooting.md](references/troubleshooting.md) covers install/import, Gym API, NumPy, long-training, and backend assumptions.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence paths for staleness checks.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) supplies structured router metadata for managed repo-skill imports.
- [scripts/check_minimal_rl_env.py](scripts/check_minimal_rl_env.py) verifies `torch`, `gym`, `numpy`, and optional CartPole/Pendulum environment creation.

## Boundaries and non-goals

- This skill does not promise benchmark performance or reproduce long training curves.
- It does not install optional GPU backends, vectorized environment libraries, or RL frameworks outside the repository's minimal examples.
- It does not turn minimalRL into a reusable package API; treat its algorithms as educational script patterns and use the bundled helpers for safe validation.
