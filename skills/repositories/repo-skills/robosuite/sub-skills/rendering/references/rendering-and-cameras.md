# Rendering and Cameras

This reference covers the verified robosuite rendering paths, camera observation keys, image conventions, and camera transform utilities.

## Renderer selection

| Goal | Minimum settings | Notes |
| --- | --- | --- |
| Headless camera observations | `has_renderer=False`, `has_offscreen_renderer=True`, `use_camera_obs=True` | Required for any camera RGB/depth/segmentation observation. |
| Interactive MuJoCo display | `has_renderer=True`, `renderer="mjviewer"` | Uses the native MuJoCo passive viewer. Only one `render_camera` is allowed here. |
| OpenCV-style display window | `has_renderer=True`, `renderer="mujoco"` | Uses the OpenCV window helper and can display multiple cameras side-by-side. |

Notes:

- `use_camera_obs=True` without an offscreen renderer raises a `ValueError`.
- If `has_renderer=True` and `renderer!="mjviewer"`, robosuite still enables the offscreen renderer internally.
- On-screen cases are display-dependent; the renderer smoke tests skip when neither `DISPLAY` nor `WAYLAND_DISPLAY` is available.
- For headless Linux runs, set `MUJOCO_GL=egl` for GPU-backed offscreen rendering or `MUJOCO_GL=osmesa` for a software fallback when needed.
- `mjviewer` is stricter about camera count: it expects a single render camera.

## Camera observation contract

The camera-related env arguments accept either a single value or per-camera lists:

| Argument | Expected form | Meaning |
| --- | --- | --- |
| `camera_names` | string or list of strings | Fixed camera names to read from. |
| `camera_heights` | int or list of ints | Image height per camera. |
| `camera_widths` | int or list of ints | Image width per camera. |
| `camera_depths` | bool or list of bools | `True` adds normalized depth observations. |
| `camera_segmentations` | `None`, string, list of strings, or nested list | Segmentation level(s): `instance`, `class`, or `element`. |

Observation keys follow this pattern:

- `<camera>_image` → RGB frame, usually `H x W x 3`
- `<camera>_depth` → normalized depth map, usually `H x W x 1`
- `<camera>_segmentation_instance` / `class` / `element` → integer label map, usually `H x W x 1`

Additional notes:

- Depth is returned in normalized MuJoCo form. Convert it to metric distance with `robosuite.utils.camera_utils.get_real_depth_map(sim, depth_map)` before geometric use.
- When any segmentation modality is enabled, robosuite shrinks sites so they do not contaminate the mask.
- `image-state` is not returned by default because image concatenation is memory-heavy. Toggle `robosuite.macros.CONCATENATE_IMAGES` if you need it.

## Image convention

robosuite exposes a global image-convention switch in `robosuite.macros`:

```python
import robosuite.macros as macros
macros.IMAGE_CONVENTION = "opencv"
```

- `"opengl"` keeps the MuJoCo/OpenGL orientation.
- `"opencv"` vertically flips returned image-based observations so they line up with imageio/OpenCV expectations.
- Set the convention before creating the env, because it affects camera observables during env construction.

Use `"opencv"` for video writing helpers unless you explicitly want to flip frames yourself.

## Camera transform utilities

The bundled `robosuite.utils.camera_utils` helpers are verified and useful for projection/backprojection workflows:

| Function | Purpose | Input/output shape expectations |
| --- | --- | --- |
| `get_camera_intrinsic_matrix(sim, camera_name, camera_height, camera_width)` | Build the 3x3 intrinsic matrix. | Returns `3 x 3`. |
| `get_camera_extrinsic_matrix(sim, camera_name)` | Build the camera pose in world coordinates. | Returns `4 x 4`. |
| `get_camera_transform_matrix(sim, camera_name, camera_height, camera_width)` | Compose world-to-pixel transform. | Returns `4 x 4`. |
| `project_points_from_world_to_camera(points, world_to_camera_transform, camera_height, camera_width)` | Project world points into pixel indices. | `points[..., 3] -> pixels[..., 2]`. |
| `transform_from_pixels_to_world(pixels, depth_map, camera_to_world_transform)` | Back-project pixels and depth into world points. | `pixels[..., 2]`, `depth_map[..., H, W, 1] -> points[..., 3]`. |
| `get_real_depth_map(sim, depth_map)` | Convert normalized MuJoCo depth to metric depth. | Input depth values must already lie in `[0, 1]`. |

Raw MuJoCo segmentation is also available via `get_camera_segmentation(sim, camera_name, camera_height, camera_width)`, which returns the two-channel simulator output. robosuite camera observations usually expose the processed single-channel key instead.

## Minimal usage pattern

```python
import robosuite as suite
from robosuite.controllers import load_composite_controller_config

env = suite.make(
    env_name="Lift",
    robots="Panda",
    controller_configs=load_composite_controller_config(controller="BASIC", robot="Panda"),
    has_renderer=False,
    has_offscreen_renderer=True,
    use_camera_obs=True,
    camera_names="agentview",
    camera_heights=64,
    camera_widths=64,
    camera_depths=True,
    camera_segmentations="instance",
)

obs = env.reset()
print(obs["agentview_image"].shape)
print(obs["agentview_depth"].shape)
print(obs["agentview_segmentation_instance"].shape)
```

If you need to tune the camera pose in XML, route to `../modeling`. If you need live human collection or USD capture from teleoperation, route to `../teleoperation`.
