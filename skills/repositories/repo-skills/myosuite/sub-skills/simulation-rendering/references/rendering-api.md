# Rendering API and operating contracts

This reference summarizes the public MuJoCo-facing interfaces used by the
MyoSuite base environment. It is intentionally independent of a source
checkout: use installed package objects and model asset paths available in the
consumer's environment.

## Handles and lifecycle

A `MujocoEnv` is constructed with a compiled `mujoco.MjModel` and one or two
`mujoco.MjData` objects:

```python
model = env.mj_model
data = env.mj_data
observed_model = env.obsd_mj_model
observed_data = env.obsd_mj_data
renderer = env.mj_renderer
```

With no separate observed model, `obsd_mj_model` and `obsd_mj_data` refer to the
same simulation handles. With partial observation/noise configurations, the
observed handles are distinct. Render the ground-truth `mj_model`/`mj_data`
through `env.mj_renderer`; observation extraction may use the observed handles.

The environment creates an `MJRenderer(model, data)`. The renderer owns a
native passive viewer (`_window`) only after `render_to_window()` is called and
owns a `mujoco.Renderer` only after `render_offscreen()` is called. Always use
`env.close()` in application code and let the renderer be cleaned up; do not
reach into private renderer fields as an application contract.

## `Renderer` interface

The abstract interface in `myosuite.renderer.renderer` exposes:

- `render_to_window()` — create/show the onscreen viewer, if supported.
- `refresh_window()` — synchronize an existing window; no-op when none exists.
- `render_offscreen(width, height, depth=False, segmentation=False,
  camera_id=-1, device_id=-1)` — return image arrays.
- `set_free_camera_settings(distance=None, azimuth=None, elevation=None,
  lookat=None, center=True)` — stage camera properties.
- `set_viewer_settings(render_tendon=None, render_actuator=None)` — stage
  tendon/actuator visualization flags.
- `close()` — release renderer resources.

`RenderMode.RGB`, `RenderMode.DEPTH`, and `RenderMode.SEGMENTATION` are declared
by the package, but the active `MJRenderer` contract uses the boolean
`rgb`/`depth`/`segmentation` arguments rather than a `mode` argument. Do not
pass `mode=RenderMode.RGB` to `MJRenderer.render_offscreen`.

## `MJRenderer.render_offscreen`

The concrete MuJoCo renderer has this effective signature:

```python
renderer.render_offscreen(
    width=640,
    height=480,
    rgb=True,
    depth=False,
    segmentation=False,
    camera_id=-1,
    device_id=-1,
)
```

Input contract:

- `width` and `height` are positive viewport dimensions in pixels.
- `rgb` requests the normal color pass.
- `depth` requests MuJoCo depth rendering.
- `segmentation` requests MuJoCo segmentation rendering.
- `camera_id=-1` selects the free camera; a string selects a named camera and
  an integer selects a numeric camera id. `None` is normalized to `-1`.
- `device_id` is part of the shared renderer interface and the visual-sensor
  path. The native `MJRenderer` creates the current MuJoCo renderer from the
  model and does not expose a separate device-selection behavior; do not claim
  CUDA rendering merely because a non-default integer was supplied.

Return contract:

| flags | return value |
|---|---|
| `rgb=True`, no other pass | RGB array, normally `uint8` with shape `(height, width, 3)` |
| `depth=True`, `segmentation=False` | `(rgb_array_or_None, depth_array)` |
| `segmentation=True`, `depth=False` | `(rgb_array_or_None, segmentation_array)` |
| both depth and segmentation | `(rgb_array_or_None, depth_array, segmentation_array)` |
| all passes false | `None` |

The depth and segmentation dtypes are supplied by MuJoCo. Check `shape` and
`dtype` at runtime rather than hard-coding a dtype in a downstream pipeline.
Segmentation is an object/element label pass, not a normal RGB image. The
renderer enables each non-RGB pass, updates the scene, renders, and disables the
pass before returning.

The renderer is cached after the first offscreen call with its initial viewport
size. Use one renderer per stable `(width, height)` configuration; if a caller
needs a different size, create a fresh environment/renderer or verify the
backend's resize behavior rather than assuming the cached object changes size.

## Cameras and viewer settings

`set_free_camera_settings` accepts:

```python
renderer.set_free_camera_settings(
    distance=2.5,
    azimuth=90,
    elevation=-30,
    lookat=[0.0, 0.0, 0.0],
    center=False,
)
```

- `azimuth` and `elevation` are degrees.
- `lookat` is a world-space three-vector.
- When `lookat` is omitted and `center=True`, the renderer computes a target
  from the median world positions of simulation geometry.
- The implementation stores `distance + 2`, so the resulting viewer distance is
  intentionally not numerically identical to the argument. Treat the argument
  as a scene framing hint.

`set_viewer_settings(render_tendon=..., render_actuator=...)` controls tendon
and actuator visualization. The same logical settings are translated into
MuJoCo scene flags for both the window and offscreen renderer. These flags alter
visualization only; they do not alter dynamics or observations.

For a named model camera, prefer a string:

```python
rgb = env.mj_renderer.render_offscreen(
    width=256, height=256, camera_id="front_cam"
)
```

If the model has no camera with that name, inspect the model's camera names or
use `camera_id=-1`. Do not use a task-specific camera name as a universal
MyoSuite guarantee.

## Environment convenience methods

`env.mj_render()` is a one-line convenience wrapper for
`env.mj_renderer.render_to_window()`. The first call launches the passive native
viewer; subsequent calls synchronize it. It does not return an image.

`env.viewer_setup(...)` calls both camera and viewer-setting methods before the
next render. The base `_setup` calls `viewer_setup()` while initializing an
environment, so explicit settings can be applied after `gym.make` and before
an onscreen render.

`env.mujoco_render_frames` controls the real-time callback path used by the
base `step` implementation. When true, action stepping may call `mj_render` as
a callback and `_forward` also renders. Avoid enabling this flag in headless
code; use direct offscreen rendering at a known cadence instead.

## Visual sensor API

`env.get_visuals(renderer=None, visual_keys=None, device_id=None)` returns a
dictionary keyed by configured visual keys, or `None` when the environment has
no `visual_keys`. It records a `time` key from `mj_data.time` and asks the robot
visual-sensor path for arrays. Key syntax is:

```text
rgb:<camera-name>:<height>x<width>:<encoder>
d:<camera-name>:<height>x<width>:<encoder>
```

The documented simple encoders are `1d` and `2d`; optional learned encoders
include `r3m18`, `r3m34`, `r3m50`, `rrl`, and `vc1` where installed. A `d:` key
is paired with its RGB request for depth. `get_obs(update_exteroception=False)`
does not refresh visuals; pass `update_exteroception=True` or call
`get_visuals` explicitly.

## Rollout/video API

`MujocoEnv.examine_policy_new` accepts:

```python
env.examine_policy_new(
    policy,
    horizon=1000,
    num_episodes=1,
    mode="exploration",       # or "evaluation"
    render="none",            # "onscreen", "offscreen", or "none"
    camera_name=None,
    frame_size=(640, 480),
    output_dir="/tmp/",
    filename="newvid",
    device_id=0,
)
```

It returns a stacked trace object. In `offscreen` mode it allocates
`(horizon, frame_height, frame_width, 3)` RGB frames and writes one MP4 per
episode using `output_dir + filename + str(episode) + ".mp4"`. Supply an output
directory with a trailing separator or use a path convention that matches this
concatenation. Keep `horizon` and `num_episodes` bounded. In `none` mode no
viewer or frame buffer is needed; in `onscreen` mode a native window is used.
For CI, the bundled PPM-producing checker is less ambiguous and has no policy
object contract.

## State/time API

- `env.dt = model.opt.timestep * env.frame_skip`.
- `env.time = env.obsd_mj_data.time`.
- `env.get_env_state()` returns copies of simulation time, generalized position
  and velocity, actuator state when present, mocap arrays when present, and
  site/body pose arrays.
- `env.set_env_state(state)` copies time, qpos, qvel, actuator, mocap, site, and
  body values into the live and observed handles where applicable, then calls
  MuJoCo stepping on both models. Call it at a controlled point in a rollout;
  restore any task-specific state through that task's own API.

After direct low-level changes, call `mujoco.mj_forward(model, data)` before
rendering or querying derived positions. A render observes the current `data`
state; it does not advance physics.
