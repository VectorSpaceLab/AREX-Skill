# Wrapper Catalog

This reference covers Gymnasium single-environment wrappers. Use vector-specific wrappers from `../vectorization/SKILL.md` instead of mixing `gymnasium.wrappers.vector` into a single-env chain.

## Chain Model

- `env = Wrapper(env, ...)` returns a new outer environment. The outermost wrapper receives `reset`, `step`, `render`, and `close` calls first.
- `env.env` is the next inner object; it may be another wrapper.
- `env.unwrapped` skips all wrappers and returns the base environment. Use it for low-level inspection, not for normal stepping, because bypassing wrappers also bypasses validation, recording, time limits, and transforms.
- `repr(env)` is useful for quick chain inspection, for example `TimeLimit<OrderEnforcing<PassiveEnvChecker<CartPoleEnv<CartPole-v1>>>>>`.
- `gymnasium.make(...)` commonly applies `PassiveEnvChecker`, `OrderEnforcing`, and `TimeLimit` from inside to outside. `disable_env_checker=True`, registration options, or `max_episode_steps` can change the default stack.

## Common and Default Wrappers

| Wrapper | Use | Notes |
| --- | --- | --- |
| `TimeLimit(env, max_episode_steps)` | Set a step cap and emit `truncated=True` when elapsed steps reach the cap. | `gymnasium.make(id, max_episode_steps=...)` is often simpler for registered envs. `max_episode_steps` must be a positive `int`. |
| `OrderEnforcing(env, disable_render_order_enforcing=False)` | Raise `ResetNeeded` if `step()` or `render()` is called before `reset()`. | Useful for catching lifecycle bugs in examples and custom envs. |
| `PassiveEnvChecker(env)` | Run passive checks on spaces, reset, step, and render outputs without modifying data. | Applied by `make` unless disabled; deeper custom env validation belongs in `../environment-api/SKILL.md`. |
| `RecordEpisodeStatistics(env, buffer_length=100, stats_key="episode")` | Add terminal episode metrics to `info` and maintain recent queues. | Use before or after pure transforms depending on whether you want transformed rewards recorded. |
| `Autoreset(env)` | Reset automatically on the step after a terminal/truncated transition. | Be explicit in training loops; it changes the usual reset responsibility. |

## Observation Wrappers

| Wrapper | Use | Space behavior |
| --- | --- | --- |
| `FlattenObservation(env)` | Convert any flattenable observation space and observations to a flat `Box`. | Uses `spaces.utils.flatten_space` and `flatten`; inspect `env.observation_space.shape` after wrapping. |
| `FilterObservation(env, filter_keys)` | Keep selected keys from `Dict` observations or indexes from `Tuple` observations. | Raises if the base observation space is not `Dict`/`Tuple`, keys are missing, indexes are invalid, or filtering leaves an empty space. |
| `TransformObservation(env, func, observation_space)` | Apply a callable to every reset/step observation. | Provide `observation_space` whenever the transform changes bounds, dtype, shape, or container type. |
| `DtypeObservation(env, dtype)` | Cast array observations to a dtype. | Keep downstream algorithms and `contains` checks in sync with the new dtype. |
| `RescaleObservation(env, min_obs, max_obs)` | Rescale `Box` observations into a new numeric range. | Requires a `Box` observation space. |
| `ReshapeObservation(env, shape)` | Reshape array observations. | New shape must be compatible with the original flattened size. |
| `GrayscaleObservation(env, keep_dim=False)` | Convert RGB image observations to grayscale. | Requires `Box` images with shape `(H, W, 3)`, bounds `[0, 255]`, and dtype `uint8`. |
| `ResizeObservation(env, shape)` | Resize image observations. | Requires OpenCV from the `other` extra and image-compatible observations. |
| `AddRenderObservation(env, render_only=True, render_key="pixels", obs_key="state")` | Add rendered frames to observations. | Requires a render mode that returns arrays; update observation handling for `Dict` outputs. |
| `TimeAwareObservation(env, flatten=True, normalize_time=False)` | Add current timestep to observations. | Needs a known `max_episode_steps` from `env.spec` or an inner `TimeLimit`. |
| `DelayObservation(env, delay)` | Return zero observations until delayed observations become available. | Delay must be a nonnegative integer. |
| `FrameStackObservation(env, stack_size, padding_type="reset")` | Stack recent observations. | Useful for pixel/state history; check resulting shape and memory footprint. |
| `NormalizeObservation(env, epsilon=...)` | Normalize observations with running statistics. | Stateful; behavior changes as statistics update. |
| `MaxAndSkipObservation(env, skip)` | Repeat actions and max-pool recent frames. | Mostly for image/Atari-style preprocessing. |
| `DiscretizeObservation(env, bins, multidiscrete=False)` | Discretize continuous `Box` observations. | Requires finite bounds. |

## Action Wrappers

| Wrapper | Use | Space behavior |
| --- | --- | --- |
| `ClipAction(env)` | Clip incoming continuous actions to the inner `Box` bounds. | Wrapper action space becomes an unbounded `Box` with the same shape/dtype because callers may provide out-of-range actions. |
| `RescaleAction(env, min_action, max_action)` | Present a new `Box` action range and map it to the inner environment's range. | Inner action space must be `Box`; scalar or array min/max must be shape-compatible. |
| `TransformAction(env, func, action_space)` | Apply a callable before passing actions inward. | Provide `action_space` for the caller-facing domain. |
| `DiscretizeAction(env, bins, multidiscrete=False)` | Present discrete bins for a continuous `Box` action space. | Can produce `Discrete` or `MultiDiscrete` action spaces. |
| `StickyAction(env, repeat_action_probability)` | Repeat the previous action with a probability. | Stateful stochastic wrapper; seed the environment and action space for reproducibility. |
| `RepeatAction(env, repeat)` | Repeat the same action for multiple inner steps. | Accumulates reward and stops early on termination/truncation. |

## Reward Wrappers

| Wrapper | Use | Notes |
| --- | --- | --- |
| `TransformReward(env, func)` | Apply a callable to each reward returned from `step()`. | Use for simple scaling/shaping when no `info` access is needed. |
| `ClipReward(env, min_reward=None, max_reward=None)` | Clip rewards to numeric bounds. | At least one bound must be provided; `min_reward` must not exceed `max_reward`. |
| `NormalizeReward(env, gamma=..., epsilon=...)` | Normalize immediate rewards using running return variance. | Stateful and training-oriented; recorded statistics outside this wrapper see normalized rewards. |

## Rendering, Video, and Pixel Wrappers

- `RecordVideo` records frames to MP4. See [recording-and-rendering.md](recording-and-rendering.md).
- `RenderCollection` changes `render()` to return a list of frames collected since reset/step calls.
- `HumanRendering` displays `rgb_array`, `rgb_array_list`, `depth_array`, or `depth_array_list` output in a window and reports `render_mode == "human"`.
- `AddWhiteNoise` and `ObstructView` modify rendered/pixel observations and require compatible pixel arrays.

## Atari and Array Conversion Wrappers

- `AtariPreprocessing` implements common ALE preprocessing such as no-op reset, frame skip, grayscale, scale, and resize. It expects an Atari/ALE environment and OpenCV; creating ALE env IDs usually requires the Atari plugin/extra.
- `ArrayConversion`, `JaxToNumpy`, `JaxToTorch`, and `NumpyToTorch` convert actions/observations across array namespaces. They require optional `array-api`, `jax`, or `torch` dependencies and should be added only when the environment and model framework need them.

## Ordering Heuristics

1. Start from environment construction/default wrappers.
2. Add action wrappers before the policy sees `env.action_space`, so the policy samples/outputs the wrapper-facing action domain.
3. Add observation wrappers before initializing models or replay buffers, so shape/dtype assumptions use the final `env.observation_space`.
4. Put `RecordEpisodeStatistics` outside reward transforms if you want transformed returns; put it inside reward transforms if you want original environment returns.
5. Put `RecordVideo` outside wrappers whose `render()` output you want captured; make sure no code drains a `RenderCollection` frame list before `RecordVideo` captures frames.
6. Use `env.close()` after video or human rendering to flush files and windows.
