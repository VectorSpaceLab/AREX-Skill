# Wrappers and observations

Use this reference when a prompt asks for normalized actions, action noise, pixel observations, reward visualization, flattened observations, or timing probes.

## Recommended wrapper order

1. Load the suite environment.
2. Set `env.task.visualize_reward = True` or pass `visualize_reward=True` to `suite.load(...)` if you want reward-colored renders.
3. Wrap action transforms first.
4. Add pixel observations last.
5. Add profiling only when you need timing data.

A practical order is:

Replace the example action range with the range your policy emits; the wrapper converts that range into the environment's native action bounds.

```python
from dm_control import suite
from dm_control.suite.wrappers import action_scale, action_noise, pixels, mujoco_profiling

env = suite.load("cartpole", "balance", environment_kwargs={"flat_observation": True})
env = action_scale.Wrapper(env, minimum=-1.0, maximum=1.0)
env = action_noise.Wrapper(env, scale=0.02)
env = pixels.Wrapper(env, pixels_only=False, render_kwargs={"height": 240, "width": 320})
env = mujoco_profiling.Wrapper(env)
```

## Action wrappers

### `action_scale.Wrapper(env, minimum, maximum)`

Use this when your policy emits normalized actions and you want to rescale them to the wrapped environment's action range.

Important constraints:

- The wrapped environment must expose a single `dm_env.specs.BoundedArray` action spec.
- The wrapped action bounds must be finite.
- `minimum` and `maximum` must be finite and broadcastable to the action shape.

Typical behavior:

- The wrapper changes the public action spec to the new range.
- Incoming actions are mapped back into the wrapped environment's original action range.

### `action_noise.Wrapper(env, scale=0.01)`

Use this when you want Gaussian exploration noise on top of the current action stream.

Important constraints:

- The wrapped environment must expose finite action bounds.
- Noise is scaled by the wrapped action range.
- Noisy actions are clipped before being passed through.
- The wrapper uses `env.task.random` for its RNG.

### Choosing between scaling and noise

- If you want to add noise in the *final physical action space*, place `action_noise` inside the `action_scale` wrapper chain.
- If you want to add noise in the *normalized policy space*, apply `action_noise` before `action_scale`.

## Observation wrappers

### `pixels.Wrapper(env, pixels_only=True, render_kwargs=None, observation_key='pixels')`

Use this when you need rendered frames alongside or instead of state observations.

Behavior to remember:

- `pixels_only=True` keeps only the rendered frame.
- `pixels_only=False` keeps the original observations and appends pixels.
- If the wrapped environment returns a single array, the wrapper stores it under the key `state` when `pixels_only=False`.
- `render_kwargs` are passed directly to `physics.render(...)`.
- The wrapper builds its observation spec from the initial rendered frame.

Common failure modes:

- The wrapped environment must expose either a single array observation spec or a mapping of array specs.
- If `pixels_only=False`, `observation_key` cannot collide with an existing key or with `state` for single-array observations.
- Rendering depends on a working MuJoCo OpenGL backend.

### `mujoco_profiling.Wrapper(env, observation_key='step_timing')`

Use this when you need simple step profiling instead of a camera image.

Behavior to remember:

- It enables profiling on the underlying physics object.
- It adds an observation entry with shape `(2,)` and dtype `float64`.
- The two numbers are the step timer duration and call count.

## Flat observations

### `control.flatten_observation(observation, output_key='observations')`

Use this when you want a single state vector instead of a dict-like observation.

Important rules:

- The input must be a mutable mapping.
- Ordered mappings keep their order.
- Other mappings are sorted by key before concatenation.
- The result is a one-entry mapping with the flattened array under `observations` by default.

### When to use `flat_observation=True`

If you are loading a suite task and want the environment to emit flat observations, pass `environment_kwargs={"flat_observation": True}` to `suite.load(...)`.

That is the quickest way to get a single state vector without manually flattening each step.

## Reward visualization

`visualize_reward=True` is not a wrapper. It is a suite load option and a task property.

- Set it at load time, or set `env.task.visualize_reward = True` before the first reset.
- When enabled, reward-colored geoms are updated during `reset()` and `step()`.
- The colors only matter if you also render frames.

## Backend caveats for pixel observations

Pixel observations call `physics.render(...)`.

- Headless systems usually need an EGL backend.
- Windowed rendering usually needs GLFW and a display.
- Software rendering usually needs OSMesa.
- If rendering fails, treat it as a backend setup issue rather than a suite-loading issue.
- For backend selection and viewer operations, use the sibling rendering skill.

## Common wrapper decisions

- Want action normalization only? Use `action_scale`.
- Want exploration noise only? Use `action_noise`.
- Want images only? Use `pixels` with `pixels_only=True`.
- Want images plus state? Use `pixels_only=False`.
- Want step timing? Use `mujoco_profiling`.
- Want a flat state vector? Use `flat_observation=True` or `control.flatten_observation(...)`.
