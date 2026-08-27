---
name: builtin-envs
description: "Choose and troubleshoot Gymnasium built-in environment families,
  optional extras, registry IDs, action masks, and render modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gymnasium Built-in Environments

Use this sub-skill when a task involves selecting or using Gymnasium's built-in environment families, deciding which optional extra is needed, inspecting registered environment IDs, handling Toy Text action masks, or diagnosing backend/render/plugin failures.

## Start Here

- Choose the smallest environment family and optional extra that matches the task; avoid `gymnasium[all]` unless a disposable environment explicitly needs every backend. See `references/optional-dependencies.md`.
- Inspect availability before installing anything: use `gym.spec("CartPole-v1")`, `gym.registry`, or `gym.pprint_registry()`; see `references/builtin-environments.md`.
- Use versioned IDs exactly, including namespaces such as `phys2d/CartPole-v1` or plugin namespaces such as `ALE/...`; do not guess unversioned names.
- For Taxi action masks and render mode choices, use `references/action-masking-and-rendering.md` and the bundled `scripts/action_mask_smoke.py`.
- For missing `pygame`, Box2D, MuJoCo, ALE/ROMs, `shimmy`, or media dependencies, use `references/troubleshooting.md` before broad installs.

## Route by Task

| Task | Read |
| --- | --- |
| Pick a built-in family or verify an env ID | [references/builtin-environments.md](references/builtin-environments.md) |
| Decide the minimal package extra | [references/optional-dependencies.md](references/optional-dependencies.md) |
| Use Taxi action masks or render modes | [references/action-masking-and-rendering.md](references/action-masking-and-rendering.md) |
| Diagnose backend, plugin, ROM, ID, or compatibility errors | [references/troubleshooting.md](references/troubleshooting.md) |
| Prove Taxi action-mask support locally | [`scripts/action_mask_smoke.py`](scripts/action_mask_smoke.py) |

## Minimum Correct Patterns

```python
import gymnasium as gym

spec = gym.spec("CartPole-v1")
print(spec.id, spec.max_episode_steps, spec.entry_point)

env = gym.make("CartPole-v1")
obs, info = env.reset(seed=123)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

```python
import gymnasium as gym

env = gym.make("Taxi-v4")
obs, info = env.reset(seed=123)
mask = info.get("action_mask")
action = env.action_space.sample(mask) if mask is not None else env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
env.close()
```

## Scope Boundaries

- Use `../environment-api/SKILL.md` for generic `Env` loops, custom environment classes, registration, `check_env`, and old Gym reset/step migration.
- Use `../vectorization/SKILL.md` for `gym.make_vec`, vectorized built-in environments, batched actions, vector wrappers, and autoreset behavior.
- Use `../wrappers-recording/SKILL.md` for `RecordVideo`, wrapper chains, recording episode statistics, and media wrapper ordering.
- Use `../spaces-data/SKILL.md` for detailed space constructors, `contains`, flattening, dtypes, and shape debugging.

Keep runtime guidance self-contained. Do not depend on Gymnasium source, tests, examples, documentation paths, or local checkout paths at runtime.
