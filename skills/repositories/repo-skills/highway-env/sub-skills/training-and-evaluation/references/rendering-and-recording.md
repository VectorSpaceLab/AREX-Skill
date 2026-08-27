# Rendering, image observations, and video recording

Use this reference when evaluation needs frames, videos, or image observations. Rendering is a runtime choice separate from the observation/action/reward configuration used by a policy.

## Render modes for evaluation

HighwayEnv follows Gymnasium render modes:

| `render_mode` | Use during training/evaluation | `env.render()` return | Display behavior |
| --- | --- | --- | --- |
| `None` | Fast training with no visual output | `None` | No window |
| `"rgb_array"` | Headless frame capture, video recording, smoke tests | `numpy.ndarray` with shape `(height, width, 3)` | No display window by default |
| `"human"` | Manual interactive viewing only | `None` | Opens a pygame window and may auto-render |

Use `render_mode="rgb_array"` for CI, remote servers, and video generation. Avoid `render_mode="human"` in training workers or headless sessions.

Since modern HighwayEnv derives offscreen rendering behavior from `render_mode`, do not rely on old `OFFSCREEN_RENDERING` environment variables. If an explicit override is needed, pass a config value such as `{"offscreen_rendering": False}` only for local debugging.

## `rgb_array` smoke pattern

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)

env = gym.make("highway-v0", render_mode="rgb_array")
obs, info = env.reset(seed=0)
frame = env.render()
assert frame is not None and frame.ndim == 3 and frame.shape[-1] == 3
for _ in range(5):
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
    frame = env.render()
    if terminated or truncated:
        break
env.close()
```

For a packaged command-line smoke test, use:

```bash
python scripts/random_policy_rollout.py --env-id highway-v0 --episodes 1 --max-steps 5 --render-rgb
```

## Recording videos with intermediate HighwayEnv frames

Gymnasium's `RecordVideo` wrapper records one frame for each `env.step(action)`. In HighwayEnv, one high-level policy action can span multiple lower-level simulation frames, so a video recorded without HighwayEnv's video-wrapper hook can look too fast or low-framerate.

Use `env.unwrapped.set_record_video_wrapper(wrapped_env)` after applying `RecordVideo` so HighwayEnv can pass intermediate simulation frames to the recorder:

```python
import gymnasium as gym
from gymnasium.wrappers import RecordVideo
import highway_env

gym.register_envs(highway_env)

env = gym.make("highway-v0", render_mode="rgb_array")
env = RecordVideo(
    env,
    video_folder="videos",
    episode_trigger=lambda episode_id: episode_id < 2,
    name_prefix="random-policy",
)
env.unwrapped.set_record_video_wrapper(env)

for episode in range(2):
    obs, info = env.reset(seed=episode)
    terminated = truncated = False
    steps = 0
    while not (terminated or truncated) and steps < 200:
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        env.render()
        steps += 1
env.close()
```

Keep `episode_trigger` narrow when testing. Recording every episode during long training creates large files and slows evaluation.

## Video timing and frame-rate fixes

If videos are too fast or show too few frames:

1. Confirm the environment was created with `render_mode="rgb_array"` before wrapping.
2. Confirm `env.unwrapped.set_record_video_wrapper(env)` is called on the wrapped environment.
3. Call `env.render()` inside the rollout loop.
4. Keep a hard step cap so a broken policy cannot record indefinitely.
5. For visually smoother recordings, tune `simulation_frequency`, `policy_frequency`, and evaluation duration intentionally rather than changing them mid-episode.

For local human viewing, `config={"real_time_rendering": True}` can sync a human window to simulation time. Do not use that for fast training or headless recording.

## Vectorized video options

For Stable-Baselines3 vectorized environments, `VecVideoRecorder` can record a fixed number of vector-env steps. It is useful for policy previews, but it does not replace the single-env `RecordVideo` pattern when you need HighwayEnv intermediate frames.

A safe approach is:

1. train with vectorized environments and no rendering;
2. load the trained model into a single `gym.make(..., render_mode="rgb_array")` environment;
3. wrap the single environment with `RecordVideo` and call `set_record_video_wrapper`;
4. run a bounded deterministic evaluation loop.

## Image observations versus videos

Image observations, such as grayscale stacks, are configured through the environment observation config and are consumed by the policy. Video recording is a rendering/output concern. They can be combined, but they do not require each other.

When training on image observations:

- validate the observation space and one reset observation shape before model creation;
- expect higher memory use and longer training than kinematics observations;
- use a CNN policy or custom feature extractor that matches the channel/height/width convention of the observation;
- keep the first training run tiny to catch shape or dtype errors.

When only recording evaluation videos, keep the policy observation unchanged and create the evaluation environment with `render_mode="rgb_array"`.
