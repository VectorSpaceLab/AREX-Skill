# Wrapper Troubleshooting

## Wrapper Order Hides Attributes

Symptoms:

- `AttributeError` appears after wrapping.
- An attribute exists on the base env but not on the outer wrapper.
- Changing `env.unwrapped.some_attr` has no visible effect because an outer wrapper overrides behavior.

Fixes:

- Print `env` or walk `env.env` to understand the chain.
- Use `env.get_wrapper_attr("name")` or `env.set_wrapper_attr("name", value)` when interacting with wrapper-aware attributes.
- Use `env.unwrapped` only for base-env inspection; do not call `step()` on `env.unwrapped` during a normal wrapped run.
- Keep wrapper-specific attributes on the wrapper instance you created if later code needs them.

## Spaces Do Not Match Transformed Data

Symptoms:

- `env.observation_space.contains(obs)` or `env.action_space.contains(action)` fails after a custom transform.
- A model/replay buffer is initialized with the wrong shape or dtype.
- `PassiveEnvChecker` warns about observations outside the declared space.

Fixes:

- For `ObservationWrapper`, set `self.observation_space` to the transformed observation contract.
- For `ActionWrapper`, set `self.action_space` to the caller-facing action contract.
- For `TransformObservation` and `TransformAction`, pass an updated `observation_space` or `action_space` when shape, dtype, bounds, or container type changes.
- Use `../spaces-data/SKILL.md` for detailed `Box`, `Dict`, `Tuple`, flattening, dtype, and `contains` work.

## `RecordVideo` Render Mode Failure

Typical error:

```text
Render mode is human, which is incompatible with RecordVideo.
Initialize your environment with a render_mode that returns an image, such as rgb_array.
```

Fix:

```python
env = gymnasium.make("CartPole-v1", render_mode="rgb_array")
env = RecordVideo(env, video_folder="videos")
```

Do not wrap an already-created `render_mode="human"` environment for video. Recreate the base environment with an image-returning render mode.

## `RecordVideo` Missing MoviePy

Typical error:

```text
MoviePy is not installed, run `pip install "gymnasium[other]"`
```

Fixes:

- Install the minimal media extra: `pip install "gymnasium[other]"`.
- If the environment is managed by a project, add the extra to that environment rather than installing unrelated heavy extras.
- If video is optional for the task, fall back to `RecordEpisodeStatistics` until media dependencies are available.

## Video Files Missing or Empty

Checklist:

- Did the trigger fire? Use `episode_trigger=lambda episode: True` for a first smoke test.
- Did the episode start with `reset()` and run at least one frame-producing step?
- Did any code call `render()` on a `RenderCollection` with `pop_frames=True` before `RecordVideo` captured frames?
- Did `env.close()` run? The final video is written on close or when recording stops.
- Is `video_folder` being overwritten or written somewhere unexpected? `RecordVideo` stores an absolute path internally.

## `HumanRendering` Fails

Symptoms:

- Assertion about accepted render modes.
- Assertion about missing `render_fps`.
- `pygame is not installed` or display/window errors.

Fixes:

- Wrap only envs created with `render_mode="rgb_array"`, `"rgb_array_list"`, `"depth_array"`, or `"depth_array_list"`.
- Prefer native `gymnasium.make(id, render_mode="human")` when the environment supports human rendering.
- Install the environment/rendering extra that provides `pygame` when needed.
- Avoid human rendering on headless machines unless a display backend is configured.

## `OrderEnforcing` Raises `ResetNeeded`

Symptoms:

- `Cannot call env.step() before calling env.reset()`.
- `Cannot call env.render() before calling env.reset()`.

Fixes:

- Always call `obs, info = env.reset(seed=...)` before `step()` or `render()`.
- If pre-reset rendering is intentionally needed, construct `OrderEnforcing(env, disable_render_order_enforcing=True)` or disable order enforcement at registration/make time when appropriate.
- Keep the wrapper during examples and tests unless it blocks a deliberate low-level diagnostic.

## Image Wrapper Shape or Dependency Errors

Common causes:

- `GrayscaleObservation` expects `Box` observations shaped `(H, W, 3)`, bounds `[0, 255]`, and dtype `uint8`.
- `ResizeObservation` imports OpenCV and raises a dependency error when `cv2` is missing; install `gymnasium[other]` for this optional dependency.
- Pixel wrappers need array observations or render frames; they are not valid for symbolic/vector observations without a preceding render-observation transform.
- Atari preprocessing expects ALE-style envs and OpenCV; route environment-family install failures to `../builtin-envs/SKILL.md`.

## Array Conversion Wrappers Missing Extras

Symptoms:

- `array_api_compat` or NumPy array API errors.
- `Jax is not installed`, `Torch is not installed`, or wrapper import failures.

Fixes:

- Install only the needed extras: `gymnasium[array-api]`, `gymnasium[jax]`, and/or `gymnasium[torch]`.
- Use `NumpyToTorch` only when PyTorch tensors are actually required by the agent code.
- Use `JaxToNumpy` or `JaxToTorch` only for JAX-backed environments.
- Keep conversion wrappers near the boundary where actions enter and observations leave the environment, then verify one reset/step type round trip.

## Wrong Wrapper Family

Symptoms:

- A vector environment is passed to a single-env wrapper or a single env is passed to a vector wrapper.
- `infos` structure errors mention vector `dict` vs list conversion.

Fixes:

- For `gym.make_vec`, `SyncVectorEnv`, `AsyncVectorEnv`, and `gymnasium.wrappers.vector.*`, use `../vectorization/SKILL.md`.
- For single-env chains, import from `gymnasium.wrappers`, not `gymnasium.wrappers.vector`.
