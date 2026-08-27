---
name: custom-components
description: "Use RL Baselines3 Zoo custom Gymnasium registrations, wrappers,
  callbacks, schedules, and algorithm registry patches safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# custom-components

Use this sub-skill when a future Researcher needs to register custom Gymnasium environments, validate wrapper/callback/policy import strings, use RL Zoo's bundled wrappers and callbacks, configure linear schedules, or patch the in-process algorithm registry for SBX or another Stable-Baselines3-compatible algorithm class.

## Start here

1. Decide what kind of component is involved:
   - Custom environment package or env id: read [custom envs, wrappers, and callbacks](references/custom-envs-wrappers-callbacks.md#custom-gymnasium-environment-registration).
   - `env_wrapper`, `vec_env_wrapper`, `callback`, `policy`, or schedule entries: read [custom envs, wrappers, and callbacks](references/custom-envs-wrappers-callbacks.md#component-configuration-flow).
   - API signatures and constraints: read [API reference](references/api-reference.md).
   - Failure diagnosis: read [troubleshooting](references/troubleshooting.md).
2. Validate import strings before launching training:

   ```bash
   python scripts/component_import_checker.py \
     --wrapper rl_zoo3.wrappers.HistoryWrapper \
     --callback rl_zoo3.callbacks.RawStatisticsCallback \
     --policy stable_baselines3.ppo.MlpPolicy
   ```

3. If components are declared in a YAML hyperparameter file, list and validate them without creating an environment:

   ```bash
   python scripts/component_import_checker.py \
     --config ./my_hyperparams.yml --env CartPole-v1
   ```

## Operating checklist

- Import custom Gymnasium registration modules before RL Zoo checks `gym.envs.registry`; for installed-package training this is normally `python -m rl_zoo3.train --gym-packages my_env_package ...` or `rl_zoo3 train --gym-packages my_env_package ...`.
- Keep custom registration modules import-only: their top-level code should call Gymnasium `register(...)` and avoid training, network calls, credentials, or heavy initialization.
- Validate every dotted import string as `module.submodule.ClassName`. Exact case matters, and the module must be importable in the same Python environment that runs RL Zoo.
- For wrappers, verify constructor kwargs and environment-space requirements before training. `HistoryWrapper`, action wrappers, and `MaskVelocityWrapper` assert on observation/action-space shape or supported env ids.
- For callbacks, verify constructor kwargs and runtime prerequisites. `RawStatisticsCallback` needs TensorBoard logging; `ParallelTrainCallback` is limited to SAC/TQC models.
- Treat SBX/JAX and external simulator packages as optional dependency surfaces; confirm they are installed before proposing commands that depend on them.

## Boundaries and routes

- Full YAML/Python hyperparameter-file grammar, indentation rules beyond wrapper/callback examples, `--conf-file`, and `--hyperparams`: route to `../config-hyperparams/SKILL.md`.
- Actual training/resume/evaluation command execution after components are validated: route to `../training-cli/SKILL.md`.
- Hyperparameter-optimization callbacks and Optuna trial behavior: route to `../tuning-optimization/SKILL.md`.
- Package install, console-entry optional plotting import behavior, and optional simulator dependencies: route to `../../references/install-and-environment.md`.

## Minimal safe workflow

```bash
# 1) Validate component imports and constructor kwargs only.
python scripts/component_import_checker.py \
  --config ./my_hyperparams.yml --env MyEnv-v0 --gym-package my_envs

# 2) If validation passes, hand off the actual run to training-cli.
python -m rl_zoo3.train --algo ppo --env MyEnv-v0 \
  --gym-packages my_envs --conf-file ./my_hyperparams.yml \
  --n-timesteps 1000 --log-folder ./runs/rl-zoo --device cpu
```

Do not train from this sub-skill unless the caller explicitly asks to execute the validated training workflow; otherwise hand off to `../training-cli/SKILL.md`.
