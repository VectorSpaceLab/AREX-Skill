---
name: vectorization
description: "Create, step, wrap, and troubleshoot Gymnasium vectorized
  environments for batched training and evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gymnasium Vectorization

Use this sub-skill when a task needs multiple Gymnasium environments stepped as one batch: `gymnasium.make_vec`, `SyncVectorEnv`, `AsyncVectorEnv`, vector wrappers, batched observations/actions/rewards/masks/infos, autoreset modes, or vector multiprocessing troubleshooting.

## Start Here

1. Prefer `gymnasium.make_vec(env_id, num_envs=..., vectorization_mode="sync" | "async")` for registered environments.
2. Use `envs.action_space.sample()` or another action batch matching `envs.action_space`; use `envs.single_action_space` only to reason about one sub-environment.
3. Treat `rewards`, `terminations`, and `truncations` as arrays of shape `(num_envs,)`, not scalar booleans.
4. Check `envs.metadata["autoreset_mode"]` before interpreting post-terminal observations or writing bootstrapping logic.
5. Use `gymnasium.wrappers.vector` wrappers around vector envs; pass single-env wrappers through `make_vec(..., wrappers=[...])` only when they should wrap each sub-environment before vectorization.
6. Always call `envs.close()`, especially for `AsyncVectorEnv` worker processes.

## Route by Task

| Task | Read |
| --- | --- |
| Create or step vector envs, choose sync vs async, handle batched outputs | [references/vector-envs.md](references/vector-envs.md) |
| Apply vector wrappers, transform batched spaces, use vector space utilities | [references/vector-wrappers-and-spaces.md](references/vector-wrappers-and-spaces.md) |
| Debug actions, masks, autoreset, multiprocessing, shared memory, render/video | [references/troubleshooting.md](references/troubleshooting.md) |
| Prove a small local vector loop works | [`scripts/vector_env_smoke.py`](scripts/vector_env_smoke.py) |

## Minimum Correct Pattern

```python
import gymnasium as gym

envs = gym.make_vec("CartPole-v1", num_envs=4, vectorization_mode="sync")
try:
    observations, infos = envs.reset(seed=123)
    actions = envs.action_space.sample()
    observations, rewards, terminations, truncations, infos = envs.step(actions)
    done_mask = terminations | truncations
finally:
    envs.close()
```

For a quick sanity check from this sub-skill directory, run `python scripts/vector_env_smoke.py --help` and then `python scripts/vector_env_smoke.py --mode sync --num-envs 2 --steps 4`.

## Scope Boundaries

- Use `../environment-api/SKILL.md` for single `Env` contracts, custom environment classes, registration, `check_env`, and non-vector reset/step migration.
- Use `../spaces-data/SKILL.md` for fundamental `Space` constructors, dtype/shape design, `contains`, flattening, and JSONable conversion.
- Use `../wrappers-recording/SKILL.md` for single-environment wrappers, recording, rendering, and custom wrapper subclassing depth.
- Use `../builtin-envs/SKILL.md` for built-in family selection, optional extras/backends, Atari/ALE, Box2D, MuJoCo, and Toy Text action masks.

Keep runtime guidance self-contained. Do not depend on the Gymnasium source tree, tests, or documentation paths at runtime.
