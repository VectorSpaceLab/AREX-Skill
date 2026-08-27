---
name: environments-and-vectorization
description: "Create and validate Gymnasium custom environments for
  Stable-Baselines3, then wrap them safely with Monitor,
  DummyVecEnv/SubprocVecEnv, VecNormalize, VecCheckNan, and frame/dict/image
  vector wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Environments And Vectorization

Use this sub-skill when the task is about Stable-Baselines3 environment compatibility rather than algorithm selection: custom Gymnasium env APIs, `check_env`, vectorized env construction, VecEnv API semantics, Monitor logging, normalization, NaN checks, frame stacking, dict/image observations, and multiprocessing caveats.

## Route By Task

- **Custom env contract or `check_env` failure**: use [references/custom-envs.md](references/custom-envs.md) for the required `reset()`/`step()` API, spaces, image/dict observations, unsupported spaces, and the validation checklist.
- **Vectorization, wrappers, or VecEnv behavior**: use [references/vectorized-envs.md](references/vectorized-envs.md) for `make_vec_env`, `DummyVecEnv`, `SubprocVecEnv`, automatic resets, `terminal_observation`, seeding/options, `VecNormalize`, `VecCheckNan`, `VecFrameStack`, and dict/image wrappers.
- **Exact signatures and wrapper matrix**: use [references/api-reference.md](references/api-reference.md) for SB3 environment helper signatures and return-value expectations.
- **Errors, warnings, and edge cases**: use [references/troubleshooting.md](references/troubleshooting.md) for reset/step shape mismatches, Gymnasium vs VecEnv API confusion, unsupported spaces, image warnings, non-zero-start spaces, NaNs/Infs, and subprocess start-method failures.
- **Quick local validation**: run `python sub-skills/environments-and-vectorization/scripts/check_custom_env.py --mode valid` or `--mode invalid` from a copied skill tree that has Stable-Baselines3 installed.

## Boundaries

- This sub-skill covers env creation, validation, wrapping, vectorization, and observation/action-space compatibility.
- For choosing PPO/SAC/DQN/A2C/TD3/DDPG/HerReplayBuffer or setting training hyperparameters, route to `training-and-algorithms`.
- For evaluation callbacks, model save/load, `VecNormalize` persistence during evaluation, or rollout metrics, route to `evaluation-and-persistence`.
- For custom policy classes, feature extractors, `MultiInputPolicy` internals, or `normalize_images=False` policy details, route to `policies-and-customization` after confirming the env observation routing here.
