# Recording and Rendering

Use `RecordEpisodeStatistics` for metrics and `RecordVideo` for MP4 files. These wrappers are independent: statistics are lightweight and base-install friendly; video needs an image render mode plus the `moviepy` dependency from `gymnasium[other]`.

## Episode Statistics

```python
import gymnasium as gym
from gymnasium.wrappers import RecordEpisodeStatistics

env = gym.make("CartPole-v1")
env = RecordEpisodeStatistics(env, buffer_length=50)
obs, info = env.reset(seed=123)
terminated = truncated = False
while not (terminated or truncated):
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())

if "episode" in info:
    print(info["episode"]["r"], info["episode"]["l"], info["episode"]["t"])
print(list(env.return_queue), list(env.length_queue), list(env.time_queue))
env.close()
```

- `info[stats_key]` appears on the step that ends an episode; default key is `"episode"`.
- `return_queue`, `length_queue`, and `time_queue` are deques bounded by `buffer_length`.
- For vector environments, route to `../vectorization/SKILL.md`; single-env `RecordEpisodeStatistics` no longer handles vector outputs.
- Wrapper order matters for rewards: statistics outside a `TransformReward`/`ClipReward` wrapper record transformed rewards, while statistics inside those wrappers record original rewards.

## Video Recording

```python
import gymnasium as gym
from gymnasium.wrappers import RecordVideo

env = gym.make("CartPole-v1", render_mode="rgb_array")
env = RecordVideo(
    env,
    video_folder="videos",
    name_prefix="eval",
    episode_trigger=lambda episode_id: episode_id % 10 == 0,
    disable_logger=True,
)
obs, info = env.reset(seed=123)
terminated = truncated = False
while not (terminated or truncated):
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

Key requirements:

- Create the base environment with an image-returning render mode such as `render_mode="rgb_array"`; `None`, `"human"`, and `"ansi"` are incompatible with `RecordVideo`.
- Install `moviepy` via the minimal extra for media helpers: `pip install "gymnasium[other]"`.
- Call `env.close()` so the final recording is written.
- Use `episode_trigger` for episode-number schedules, `step_trigger` for global-step schedules, or omit both to use Gymnasium's capped cubic schedule.
- Use `video_length=0` for whole episodes; use a positive `video_length` for fixed-length clips that may span episode boundaries.
- Set `fps` if the environment metadata lacks `render_fps` or you need a specific frame rate.

## RenderCollection

`RenderCollection(env, pop_frames=True, reset_clean=True)` wraps an image-rendering environment and makes `render()` return a list of collected frames.

- `reset()` collects the first frame; each `step()` collects another frame.
- With `pop_frames=True`, calling `render()` drains the list.
- With `pop_frames=False`, repeated `render()` calls return the same accumulated list.
- With `reset_clean=False`, frames remain across resets.
- `RecordVideo` can handle list-returning render output, but calling `render()` yourself can drain frames before recording if `pop_frames=True`.

## HumanRendering

`HumanRendering(env)` opens a window for environments that can already produce arrays.

- The wrapped environment must use `render_mode` in `"rgb_array"`, `"rgb_array_list"`, `"depth_array"`, or `"depth_array_list"`.
- The base environment metadata must include `"render_fps"`.
- It imports `pygame`; Classic Control installs usually provide this via the relevant extra.
- The wrapper renders during `reset()` and `step()`; its own `render()` returns `None`.
- If an environment natively supports `render_mode="human"`, prefer creating it directly with that render mode instead of wrapping.

## Evaluation vs Training Schedules

| Scenario | Recommended setup |
| --- | --- |
| Evaluate every episode visually | `RecordVideo(..., episode_trigger=lambda episode: True)` plus `RecordEpisodeStatistics`. |
| Training with periodic clips | `episode_trigger=lambda episode: episode % period == 0`; keep statistics on every episode. |
| Debug a transient step-level issue | `step_trigger=lambda step: step >= start and step % period == 0`, optionally with `video_length`. |
| Metrics only in fast training | Use only `RecordEpisodeStatistics`; avoid video/rendering overhead. |

## Minimal Troubleshooting Checklist

1. If `RecordVideo` raises an incompatible render-mode error, recreate the base env with `render_mode="rgb_array"` or another image mode.
2. If it raises `MoviePy is not installed`, install `gymnasium[other]` or `moviepy` in the runtime environment.
3. If files are missing or zero length, ensure the trigger fired, at least one frame was captured, and `env.close()` ran.
4. If a human window fails, check `pygame`, display availability, accepted render modes, and `render_fps` metadata.
