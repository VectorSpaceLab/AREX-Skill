---
name: wrappers-recording
description: "Apply, inspect, author, and troubleshoot Gymnasium
  single-environment wrappers, recording helpers, and rendering helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gymnasium Wrappers and Recording

Use this sub-skill when a task needs single-environment Gymnasium wrappers: applying wrapper chains, inspecting wrapped environments, writing custom wrappers, recording episode statistics or videos, and diagnosing wrapper or render-mode failures.

## Start Here

1. Build the base environment with `gymnasium.make(...)`; most made environments already include `TimeLimit<OrderEnforcing<PassiveEnvChecker<...>>>` unless the spec/options disable parts of that stack.
2. Add wrappers outside-in: `env = Wrapper(env, ...)`; the last wrapper assigned is the first object the agent interacts with.
3. Inspect `env` for the full chain, `env.env` for the next inner layer, and `env.unwrapped` for the original base environment.
4. After any wrapper that changes observations or actions, verify `env.observation_space`, `env.action_space`, `reset()`, and one `step()` agree.
5. Use `RecordEpisodeStatistics` for lightweight metrics; add `RecordVideo` only when the environment was created with image-returning rendering such as `render_mode="rgb_array"` and `moviepy` is installed.

## Route by Task

| Task | Read |
| --- | --- |
| Choose or order built-in wrappers | [references/wrapper-catalog.md](references/wrapper-catalog.md) |
| Record episode returns, lengths, videos, or render frames | [references/recording-and-rendering.md](references/recording-and-rendering.md) |
| Write `Wrapper`, `ObservationWrapper`, `ActionWrapper`, or `RewardWrapper` subclasses | [references/custom-wrappers.md](references/custom-wrappers.md) |
| Diagnose wrapper order, changed spaces, render/video, image wrapper, Atari, or array conversion errors | [references/troubleshooting.md](references/troubleshooting.md) |
| Prove a local wrapper chain works | [`scripts/wrapper_smoke.py`](scripts/wrapper_smoke.py) |

## Common Patterns

```python
import gymnasium as gym
from gymnasium.wrappers import FlattenObservation, RecordEpisodeStatistics, TimeLimit

env = gym.make("CartPole-v1")
env = TimeLimit(env, max_episode_steps=200)
env = FlattenObservation(env)
env = RecordEpisodeStatistics(env)
obs, info = env.reset(seed=123)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
```

```python
import gymnasium as gym
from gymnasium.wrappers import RecordVideo

env = gym.make("CartPole-v1", render_mode="rgb_array")
env = RecordVideo(env, video_folder="videos", episode_trigger=lambda episode: True)
```

## Boundaries

- For vector environments and `gymnasium.wrappers.vector`, use `../vectorization/SKILL.md`.
- For detailed `Space` constructor, flattening, dtype, and `contains` guidance, use `../spaces-data/SKILL.md`.
- For environment registration, `check_env`, and custom `Env` lifecycle, use `../environment-api/SKILL.md`.
- For built-in environment family extras such as Box2D, MuJoCo, Atari/ALE IDs, or Toy Text action masks, use `../builtin-envs/SKILL.md`.
