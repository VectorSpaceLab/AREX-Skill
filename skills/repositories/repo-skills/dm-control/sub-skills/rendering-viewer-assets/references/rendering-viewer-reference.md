# Rendering, pixel observations, cameras, and viewer reference

This reference covers dm_control rendering behavior for installed-package workflows. Set backend environment variables before Python imports `dm_control`, `mujoco`, `OpenGL`, or any dm_control rendering/viewer module; restart the process after changing them.

## Backend selection rules

By default, dm_control tries OpenGL backends in this order: **GLFW → EGL → OSMesa**. Pin a backend when reproducibility matters.

| Backend | Select with | Best for | Requirements and caveats | If it fails |
|---|---|---|---|---|
| Default auto | leave `MUJOCO_GL` unset | Local development where any available renderer is acceptable | Tries GLFW first, then EGL, then OSMesa. On headless hosts, the initial GLFW attempt may warn about missing `DISPLAY` even if EGL later works. | Pin `MUJOCO_GL=egl` or `MUJOCO_GL=osmesa` for deterministic headless jobs. |
| GLFW | `MUJOCO_GL=glfw` | Interactive viewer and windowed hardware rendering | Requires a windowing display; `dm_control.viewer` can only be used with GLFW. On headless Linux without `DISPLAY`, it is expected to fail. | Use EGL for headless hardware offscreen rendering, or provide a real display/windowing setup. |
| EGL | `MUJOCO_GL=egl` | Headless hardware-accelerated offscreen rendering | Requires an EGL driver with `EXT_platform_device` support. For multi-GPU systems, set `MUJOCO_EGL_DEVICE_ID=<id>` before import. | Try a different `MUJOCO_EGL_DEVICE_ID`, check driver availability, or fall back to OSMesa if software rendering is installed. |
| OSMesa | `MUJOCO_GL=osmesa` | Headless software rendering | Requires system OSMesa/OpenGL libraries. It is optional; do not assume a pip install provides the needed system library. | Use EGL when hardware drivers are available, or install the host's OSMesa packages. |

Public package installs:

```bash
python -m pip install dm_control
# For unreleased source snapshots only:
python -m pip install git+https://github.com/google-deepmind/dm_control.git
```

Do not use editable installs; dm_control documents editable mode as unsupported.

Linux public package hints from dm_control's install notes:

- GLFW/windowed rendering commonly needs `libglfw3` and GLEW.
- EGL/headless hardware rendering commonly needs GLEW and a driver that supports `EXT_platform_device`.
- OSMesa/software rendering commonly needs GLX and OSMesa libraries.

macOS Homebrew note: use a Homebrew Python and expose Homebrew libraries before running dm_control, for example:

```bash
export DYLD_LIBRARY_PATH=$(brew --prefix)/lib:$DYLD_LIBRARY_PATH
```

## Backend validation commands

From this sub-skill directory:

```bash
python scripts/render_backend_probe.py --backend default
python scripts/render_backend_probe.py --backend egl --egl-device-id 0
python scripts/render_backend_probe.py --backend osmesa
python scripts/render_backend_probe.py --backend glfw
```

Expected success signal: a line with `render_ok`, the selected backend, an RGB frame shape such as `(48, 64, 3)`, dtype `uint8`, and a numeric mean. During construction, EGL passed this probe, OSMesa was missing or unusable, and GLFW failed in a display-less headless session.

## `physics.render(...)` API

`dm_control.mujoco.Physics.render` returns NumPy pixel arrays and creates a temporary camera internally.

```python
from dm_control import suite

env = suite.load(domain_name="cartpole", task_name="balance")
time_step = env.reset()
frame = env.physics.render(height=84, width=84, camera_id=-1)
print(frame.shape, frame.dtype)  # (84, 84, 3), uint8 on RGB renders
```

Important arguments:

| Argument | Use |
|---|---|
| `height`, `width` | Output viewport size in pixels. They must fit the model's offscreen framebuffer. If needed, increase `<visual><global offwidth="..." offheight="..."/></visual>` in the MJCF model. |
| `camera_id` | `-1` uses MuJoCo's free camera. A nonnegative integer or camera name selects a fixed camera defined in the model. String camera names must exist. |
| `depth=True` | Returns a `(height, width)` `float32` array of depth in meters. Cannot be combined with segmentation, overlays, or render flag overrides. |
| `segmentation=True` | Returns a `(height, width, 2)` `int32` array containing object ID and MuJoCo object type labels; background is `(-1, -1)`. Cannot be combined with depth, overlays, or render flag overrides. |
| `overlays=(...)` | Sequence of `dm_control.mujoco.TextOverlay` instances for text on RGB renders only. |
| `scene_option=...` | A `dm_control.mujoco.wrapper.MjvOption` for custom visualization options. |
| `render_flag_overrides={...}` | Rendering flag overrides such as `{"wireframe": True}` for RGB renders only. |
| `scene_callback=...` | Callback called after the scene is built and before rendering, useful for adding temporary geoms to a scene. |

Depth and segmentation are mutually exclusive. If overlays or render flag overrides are requested with depth/segmentation, dm_control raises `ValueError`.

## Camera helper classes

For one-off frames, `physics.render(...)` is simplest. Use camera classes when you need camera matrices, repeated renders from one camera, overlays, or a movable free camera.

```python
import numpy as np
from dm_control import mujoco

camera = mujoco.MovableCamera(env.physics, height=120, width=160)
camera.set_pose(lookat=np.array([0.0, 0.0, 0.2]), distance=2.0,
                azimuth=90.0, elevation=-30.0)
overlay = mujoco.TextOverlay(title="cartpole", body="debug frame")
frame = camera.render(overlays=[overlay])
projection = camera.matrix
```

Concepts:

- `mujoco.Camera` binds a physics object, image size, and `camera_id`. It can return a camera matrix via `camera.matrix`.
- `mujoco.MovableCamera` is always a free camera (`camera_id=-1`) and supports `get_pose()` / `set_pose(...)`.
- `mujoco.TextOverlay` draws title/body text into RGB renders at positions such as `"top left"`; overlays are not valid with depth or segmentation renders.

## Pixel observation workflow

The Control Suite pixel wrapper renders immediately during wrapper construction to build the observation spec. Therefore backend errors surface before the first reset.

```python
from dm_control import suite
from dm_control.suite.wrappers import pixels

env = suite.load("cartpole", "balance")
env = pixels.Wrapper(
    env,
    pixels_only=False,
    render_kwargs={"height": 84, "width": 84, "camera_id": -1},
    observation_key="pixels",
)
time_step = env.reset()
print(time_step.observation["pixels"].shape)
```

Rules and caveats:

- Probe rendering first with `scripts/render_backend_probe.py`; then run the pixel-wrapped process with the same backend setting.
- `pixels_only=True` discards original observations. Use `pixels_only=False` when state and image observations are both needed.
- `observation_key` must not collide with existing observation keys; use a custom key such as `"front_pixels"` for multiple wrappers.
- Fixed cameras require the model to define them. If in doubt, use `camera_id=-1` for the free camera or inspect available camera names through the model API.
- Pixel wrappers belong to suite-style RL loops; route reward/spec/rollout questions to `suite-rl-workflows` after backend validation.

## Viewer launch patterns

`dm_control.viewer.launch(environment_loader, policy=None, title="Explorer", width=1024, height=768)` opens an interactive window. It accepts either an environment instance or a callable returning an environment. The optional policy accepts a `TimeStep` and returns an action matching `environment.action_spec()`.

Use the bundled safe template first:

```bash
python scripts/viewer_launch_template.py --family suite --domain cartpole --task balance
python scripts/viewer_launch_template.py --family suite --domain cartpole --task balance --policy random --launch
python scripts/viewer_launch_template.py --family manipulation --manipulation-env <environment_name> --launch
```

The default is dry-run and does not import the viewer or open a GUI. Only pass `--launch` when a real display/windowing setup is available. For remote sessions, notebooks, CI, or containers without display forwarding, prefer offscreen `physics.render` plus EGL/OSMesa.

Suite loader pattern:

```python
from dm_control import suite
from dm_control import viewer


def loader():
    return suite.load(domain_name="cartpole", task_name="balance")

viewer.launch(loader, title="cartpole.balance")
```

Manipulation loader pattern:

```python
from dm_control import manipulation
from dm_control import viewer


def loader():
    return manipulation.load(environment_name="<environment_name>")

viewer.launch(loader, title="manipulation")
```

Policy pattern:

```python
import numpy as np

env_for_spec = loader()
action_spec = env_for_spec.action_spec()


def random_policy(time_step):
    del time_step
    return np.random.uniform(action_spec.minimum, action_spec.maximum,
                             size=action_spec.shape)
```

Create the final policy from the same environment specification as the launched environment. If the environment has stochastic task construction, keep seeding explicit in the loader.
