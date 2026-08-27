---
name: environment-api
description: "Use Gymnasium's single-environment API:
  make/reset/step/render/close loops, custom Env classes, registration/specs,
  checker validation, seeding, and old Gym migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gymnasium Environment API

Use this sub-skill when a task involves creating or interacting with a single Gymnasium `Env`, migrating old Gym code, registering a custom environment, inspecting `EnvSpec`, or fixing `reset`/`step`/`check_env` failures.

## Start Here

- For a basic loop, use `gymnasium.make(...)`, `obs, info = env.reset(...)`, and `obs, reward, terminated, truncated, info = env.step(action)`; see `references/api-reference.md`.
- For custom environments, subclass `gymnasium.Env`, define `action_space` and `observation_space`, call `super().reset(seed=seed)`, and validate with `check_env`; see `references/custom-environments.md`.
- For migration from old Gym, update imports, reset return unpacking, seeding, render mode placement, and the `done` split; see `references/migration-and-validation.md`.
- For common errors and warnings, use `references/troubleshooting.md` before changing unrelated code.
- To smoke-test a minimal custom env from this sub-skill directory, run `python scripts/check_custom_env.py --help` and then `python scripts/check_custom_env.py`.

## Scope Boundaries

- Use `../spaces-data/SKILL.md` for detailed space constructors, flattening, JSON conversion, dtype/shape design, and `contains` diagnostics.
- Use `../wrappers-recording/SKILL.md` for wrapper catalogs, wrapper subclassing depth, recording videos, rendering wrappers, and media dependencies.
- Use `../vectorization/SKILL.md` for `gym.make_vec`, `SyncVectorEnv`, `AsyncVectorEnv`, batched actions/observations, and vector wrappers.
- Use `../builtin-envs/SKILL.md` for choosing built-in environment families, optional extras, Atari/ALE, Box2D, MuJoCo, Toy Text masks, and plugin install issues.

## Minimum Correct Patterns

```python
import gymnasium as gym

env = gym.make("CartPole-v1")
obs, info = env.reset(seed=123)
terminated = truncated = False
while not (terminated or truncated):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
env.close()
```

```python
from gymnasium.utils.env_checker import check_env

check_env(raw_env, skip_render_check=True)
```

Keep public runtime guidance self-contained. Do not depend on the Gymnasium source tree, test tree, or documentation paths at runtime.
