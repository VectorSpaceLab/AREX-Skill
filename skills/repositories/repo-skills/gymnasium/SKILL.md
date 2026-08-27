---
name: gymnasium
description: "Use Gymnasium for reinforcement-learning environment loops,
  spaces, wrappers, vectorized envs, built-in environment families, and
  Gym-to-Gymnasium migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gymnasium

Use this repo skill when a task involves Gymnasium's reinforcement-learning environment API: creating `Env` loops, authoring custom environments, selecting action/observation spaces, applying wrappers, recording episodes, vectorizing envs, choosing built-in environments, or migrating older Gym code.

## Quick Start

```python
import gymnasium as gym

env = gym.make("CartPole-v1")
try:
    obs, info = env.reset(seed=123)
    terminated = truncated = False
    while not (terminated or truncated):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
finally:
    env.close()
```

If a task only needs an install/import sanity check, run the bundled smoke helper:

```bash
python scripts/gymnasium_smoke.py --help
python scripts/gymnasium_smoke.py
```

## Route by Task

| User task | Read |
| --- | --- |
| Basic `gym.make`, `reset`, `step`, `render`, custom `Env`, registration, `EnvSpec`, `check_env`, seeding, or old Gym migration | [sub-skills/environment-api/SKILL.md](sub-skills/environment-api/SKILL.md) |
| Design `action_space`/`observation_space`, debug `contains`, flatten/unflatten observations, JSONable conversion, dtype/shape issues | [sub-skills/spaces-data/SKILL.md](sub-skills/spaces-data/SKILL.md) |
| Apply wrapper chains, write custom wrappers, record videos/statistics, use render helpers, troubleshoot wrapper order or media dependencies | [sub-skills/wrappers-recording/SKILL.md](sub-skills/wrappers-recording/SKILL.md) |
| Use `gym.make_vec`, `SyncVectorEnv`, `AsyncVectorEnv`, batched actions/infos/masks, autoreset modes, vector wrappers, multiprocessing issues | [sub-skills/vectorization/SKILL.md](sub-skills/vectorization/SKILL.md) |
| Choose Classic Control, Toy Text, Box2D, MuJoCo, Atari/ALE, optional extras, versioned IDs, action masks, render modes | [sub-skills/builtin-envs/SKILL.md](sub-skills/builtin-envs/SKILL.md) |

## Install and Extras

Start with the base package unless the selected environment family or wrapper explicitly needs an extra:

```bash
pip install gymnasium
```

Read [references/installation-and-extras.md](references/installation-and-extras.md) before installing optional dependencies. Prefer the smallest matching extra, such as `gymnasium[classic-control]`, `gymnasium[toy-text]`, `gymnasium[box2d]`, `gymnasium[mujoco]`, `gymnasium[atari]`, or `gymnasium[other]`, instead of `gymnasium[all]` in ordinary agent tasks.

## API Rules That Prevent Most Bugs

- `Env.reset(seed=..., options=...)` returns `(observation, info)`; seed through `reset`, not `env.seed(...)`.
- `Env.step(action)` returns `(observation, reward, terminated, truncated, info)`; use `terminated or truncated` to end an episode, but use `terminated` alone for value bootstrapping decisions.
- Pass render mode to `gym.make(..., render_mode="rgb_array")` or `"human"`; do not call old `env.render(mode=...)` code.
- Sample vector-environment actions from `envs.action_space`, not `envs.single_action_space`, unless you are building the full action batch yourself.
- Inspect registered IDs with `gym.spec(...)`, `gym.registry`, or `gym.pprint_registry()` before guessing environment names.

## Cross-cutting Troubleshooting

Use [references/troubleshooting.md](references/troubleshooting.md) for package-level issues such as import confusion, old Gym migration, missing optional extras, invalid environment IDs, render/video failures, checker warnings, vectorization mistakes, and wrapper/space mismatches.

## Provenance

This skill was generated from the Gymnasium source state recorded in [references/repo-provenance.md](references/repo-provenance.md). If the source repository changes, refresh this skill before relying on exact API, wrapper, or optional-dependency details.
