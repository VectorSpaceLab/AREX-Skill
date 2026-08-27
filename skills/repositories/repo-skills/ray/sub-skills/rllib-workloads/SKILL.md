---
name: rllib-workloads
description: "Use Ray RLlib for AlgorithmConfig and PPOConfig workloads,
  Gymnasium environments, EnvRunner and Learner scaling, Tune sweeps,
  checkpoints, evaluation, and RLlib troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray RLlib Workloads

Use this sub-skill when the task mentions `ray.rllib`, `PPOConfig`, `AlgorithmConfig`, `environment()`, `env_runners()`, `learners()`, `training()`, `evaluation()`, `build_algo()`, `algo.train()`, Gymnasium environments, `register_env`, multi-agent RL, offline RL, RLlib with Tune, RLlib checkpoints, or action/observation spaces.

## Fast Routing

- Start with `PPOConfig` or another algorithm-specific config, then chain builder methods before calling `validate()`, `build_algo()`, or Tune.
- Use config-only checks before expensive training: import RLlib, define the env, call `.environment(...)`, set low local resources, and call `config.validate()`.
- Register custom environments with `ray.tune.registry.register_env` when EnvRunner actors must construct them remotely; do not rely on Gymnasium's local registry for distributed RLlib runs.
- Use `env_runners(...)` for sample-collection actors and vectorized env copies, `learners(...)` for learner scaling, and `training(...)` for PPO-specific hyperparameters.
- Route generic Tune search-space, scheduler, result-grid, and storage concepts to `../train-tune/SKILL.md`; route generic Ray resource and runtime issues to `../core-runtime/SKILL.md`; route serving trained policies to `../serve-deployments/SKILL.md`.

## Minimal Config Pattern

```python
from ray.rllib.algorithms.ppo import PPOConfig

config = (
    PPOConfig()
    .environment("CartPole-v1")
    .env_runners(num_env_runners=0)
    .training(lr=5e-5, train_batch_size_per_learner=256)
)
config.validate()
```

## Read Next

- Read `references/api-reference.md` for `AlgorithmConfig` and `PPOConfig` builder methods, defaults, lifecycle, and result objects.
- Read `references/workflows.md` for installation, custom Gymnasium envs, PPO train/evaluate/checkpoint patterns, Tune sweeps, and config-only validation.
- Read `references/troubleshooting.md` for missing extras, env registration, Gymnasium API tuple returns, space mismatches, expensive training, cleanup, and Tune resource/metric issues.
- Run `python scripts/rllib_config_smoke.py --help` for a safe helper. Add `--validate` to import RLlib and validate a tiny custom-env PPO config without long training.

## Installation Notes

- Prefer narrow extras: `ray[rllib]` for RLlib workloads. Add `torch` when examples or algorithms need the default PyTorch backend.
- Add heavy environment packages only when the selected workload requires them, such as Atari ROM support, MuJoCo, Box2D, or PettingZoo; do not install them by default.
- Python support for this Ray family is `>=3.10`.
- Avoid recommending `ray[all]` by default; it can install unrelated Ray libraries and heavy optional dependencies.
