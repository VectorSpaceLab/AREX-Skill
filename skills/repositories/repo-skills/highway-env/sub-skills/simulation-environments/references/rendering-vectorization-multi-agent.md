# Rendering, vectorization, and multi-agent operation

Use this reference for HighwayEnv rendering modes, `RecordVideo`, vectorized Gymnasium environments, subprocess registration, and multi-agent intersection semantics.

## Rendering modes

HighwayEnv follows Gymnasium's render-mode convention.

| `render_mode` | Window behavior | `env.render()` return | Step/reset auto-render |
|---|---|---|---|
| `None` | No window | `None` and a warning if called | No |
| `"rgb_array"` | Off-screen pixel rendering | NumPy array shaped `(screen_height, screen_width, 3)` | No |
| `"human"` | Opens a pygame window | `None` | Yes |

Use `render_mode="rgb_array"` for headless automation, images, tests, and video recording. Use `render_mode="human"` only for interactive viewing on a machine with display support.

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)

env = gym.make(
    "highway-v0",
    render_mode="rgb_array",
    config={"screen_width": 320, "screen_height": 160, "duration": 3},
)
try:
    obs, info = env.reset(seed=0)
    frame = env.render()
    assert frame.shape == (160, 320, 3)
finally:
    env.close()
```

In current HighwayEnv behavior, `offscreen_rendering` defaults to `None` and is derived from `render_mode`. The old `OFFSCREEN_RENDERING` environment variable is deprecated and ignored; choose the render mode explicitly instead.

## RGB rollout pattern

```python
env = gym.make("merge-v1", render_mode="rgb_array", config={"duration": 3})
frames = []
try:
    obs, info = env.reset(seed=0)
    frames.append(env.render())
    for _ in range(10):
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        frames.append(env.render())
        if terminated or truncated:
            break
finally:
    env.close()
```

For generic utilities, check that `render()` returned an array before using `.shape`, because `human` and `None` render modes return `None`.

## RecordVideo pattern

Gymnasium's `RecordVideo` wrapper captures calls to `render()`. HighwayEnv can also capture intermediate physics frames between policy decisions if the wrapper is registered with the unwrapped env.

```python
import gymnasium as gym
from gymnasium.wrappers import RecordVideo
import highway_env

gym.register_envs(highway_env)

base_env = gym.make("highway-v0", render_mode="rgb_array", config={"duration": 5})
env = RecordVideo(
    base_env,
    video_folder="videos",
    episode_trigger=lambda episode_id: True,
)
env.unwrapped.set_record_video_wrapper(env)
try:
    obs, info = env.reset(seed=0)
    for step_index in range(20):
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        if terminated or truncated:
            break
finally:
    env.close()
```

Notes:

- Use `render_mode="rgb_array"`; `human` mode does not return frames for video wrappers.
- Call `env.unwrapped.set_record_video_wrapper(env)` after wrapping so HighwayEnv can capture intermediate simulation frames, not only policy-decision frames.
- Keep videos short in smoke checks by setting `duration` and a step cap.
- Store videos in a caller-chosen relative folder; this sub-skill does not require repository-local data.

## Vectorized environments

Gymnasium vector environments work when each worker creates its own HighwayEnv instance. Keep per-env configs consistent enough that observations, rewards, and `info` values can be stacked by Gymnasium.

```python
import gymnasium as gym
import numpy as np
import highway_env

gym.register_envs(highway_env)

def make_env(duration):
    def thunk():
        return gym.make(
            "highway-v0",
            config={"duration": duration, "simulation_frequency": 2, "vehicles_count": 5},
        )
    return thunk

envs = gym.vector.SyncVectorEnv(
    [make_env(2), make_env(3)],
    autoreset_mode="SameStep",
)
try:
    obs, info = envs.reset(seed=0)
    action = envs.action_space.sample()
    obs, reward, terminated, truncated, info = envs.step(action)
finally:
    envs.close()
```

A native dtype-sensitive check uses numeric `info["speed"]` values and confirms they stack as floating arrays. If custom wrappers add object-valued or inconsistent info entries, vectorization may fail or produce object arrays.

For simple discrete vector smoke tests, a zero action can be built from the vector action space:

```python
zero_action = np.zeros(envs.action_space.shape, dtype=envs.action_space.dtype)
obs, reward, terminated, truncated, info = envs.step(zero_action)
```

For continuous or tuple/multi-agent spaces, prefer `envs.action_space.sample()` unless you know the exact batched structure.

## Multiprocessing and spawn/forkserver workers

Child processes started by `spawn` or `forkserver` do not inherit module imports from the parent. If a worker calls `gym.make("highway-v0")` without importing `highway_env`, Gymnasium may raise a name lookup error. Use one of these safe patterns inside the worker:

```python
# Pattern A: module-qualified ID triggers import in the child.
env = gym.make("highway_env:highway-v0")
```

```python
# Pattern B: explicit import in the worker factory.
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)
env = gym.make("highway-v0")
```

Close environments before worker exit to release rendering/viewer resources.

## Multi-agent configuration on ordinary environments

Most HighwayEnv scenarios can be configured with multiple controlled vehicles. A normal single-agent environment only applies a single action unless you also configure multi-agent observation/action types.

```python
env = gym.make(
    "highway-v0",
    render_mode="rgb_array",
    config={
        "controlled_vehicles": 2,
        "vehicles_count": 1,
        "observation": {
            "type": "MultiAgentObservation",
            "observation_config": {"type": "Kinematics"},
        },
        "action": {
            "type": "MultiAgentAction",
            "action_config": {"type": "DiscreteMetaAction"},
        },
    },
)
obs, info = env.reset(seed=0)
action = tuple(env.action_space.spaces[i].sample() for i in range(len(env.action_space.spaces)))
obs, reward, terminated, truncated, info = env.step(action)
```

Detailed observation/action nested config belongs to the observations-actions-rewards sub-skill.

## Registered multi-agent intersection variants

The intersection family has dedicated multi-agent IDs:

| ID | Wrapper status | Connected-lane neighbour search | Return semantics |
|---|---:|---:|---|
| `intersection-multi-agent-v0` | No registered `MultiAgentWrapper` | No | Cooperative scalar reward and scalar termination, plus `info["agents_rewards"]` and `info["agents_terminated"]`. |
| `intersection-multi-agent-v1` | Registered `MultiAgentWrapper` | No | `reward` is the tuple from `info["agents_rewards"]`; `terminated` is the tuple from `info["agents_terminated"]`; `truncated` stays scalar/bool-like. |
| `intersection-multi-agent-v2` | Registered `MultiAgentWrapper` | Yes | Same wrapper semantics as `v1`; preferred for new multi-agent experiments. |

The wrapper variants intentionally do not match Gymnasium's single-agent API checker expectations because rewards and terminations are per-agent tuples. Handle done logic with `any(...)` or `all(...)` according to your algorithm's convention.

```python
env = gym.make("intersection-multi-agent-v2")
try:
    obs, info = env.reset(seed=0)
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    any_agent_done = any(terminated) if isinstance(terminated, tuple) else bool(terminated)
finally:
    env.close()
```

For centralized training, a common pattern is to dispatch each tuple observation to a policy, build a tuple of actions, step once, and then update per-agent learners with `obs_i`, `action_i`, `next_obs_i`, the appropriate reward component, and the chosen done convention.
