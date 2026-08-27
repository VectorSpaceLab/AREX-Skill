# Kaolin visualization API reference

This reference summarizes the visualization APIs and behaviors needed for operating tasks. It is self-contained; do not reopen the source repository for ordinary use.

## Optional dependency map

| Capability | Main imports | Required or common optional packages | Safe probe |
|---|---|---|---|
| Timelapse USD writing/parsing | `kaolin.visualize.Timelapse`, `TimelapseParser`, `kaolin.io.usd` | OpenUSD Python module `pxr`; Kaolin USD I/O dependencies | `python - <<'PY'\nfrom pxr import Usd\nprint('pxr ok')\nPY` |
| Dash3D server | `kaolin.experimental.dash3d.run`, Flask, Tornado, `pxr` | `flask`, `tornado`, browser with WebGL; `pxr` for USD reading | `python scripts/kaolin_dash3d_help.py --check-imports` |
| Jupyter interactive visualizers | `kaolin.visualize.IpyTurntableVisualizer`, `IpyFirstPersonVisualizer` | `ipycanvas`, `ipyevents`, `ipywidgets`, `comm`, `jupyter_client`; renderer-specific packages | `python - <<'PY'\nimport ipycanvas, ipyevents, ipywidgets\nprint('ipy widgets ok')\nPY` |
| `quick_viz` image grid | `kaolin.visualize.quick_viz` | `matplotlib`, `torchvision`, `PIL` | `python - <<'PY'\nimport matplotlib, torchvision, PIL\nprint('quick_viz deps ok')\nPY` |
| GLTF interactive visualizer | `kaolin.io.gltf`, `kaolin.render.easy_render`, `kaolin.visualize` | GLTF/material I/O dependencies; rendering may require CUDA/nvdiffrast depending on chosen renderer | Probe IO and rendering separately; route render backend issues to rendering sub-skill |

## Timelapse writer

Verified constructor:

```python
kaolin.visualize.Timelapse(log_dir, up_axis="Y")
```

Important behavior:

- `log_dir` is the root directory that receives category subdirectories and USD files.
- The inspected implementation stores `log_dir` as `timelapse.logdir`. The `up_axis` parameter is accepted by the constructor; no log-directory layout behavior depends on it in the inspected implementation.
- Timelapse writes one USD file per item per category/type, and appends time samples into the same file when called again at later `iteration` values.
- All non-`None` list arguments in one call must have equal length. Supplying no data attributes raises an assertion.
- Use distinct `category` names when you need multiple independent batches for the same object type.

### `add_mesh_batch`

Signature shape:

```python
timelapse.add_mesh_batch(
    iteration=0,
    category="",
    vertices_list=None,
    faces_list=None,
    uvs_list=None,
    face_uvs_idx_list=None,
    face_normals_list=None,
    materials_list=None,
)
```

Expected inputs and outputs:

| Argument | Meaning | Notes |
|---|---|---|
| `iteration` | Time code to author in USD | Use integer training iteration values; default `0` works for fixed data. |
| `category` | Directory/group name under `log_dir` | Examples: `ground_truth`, `input`, `output`, `prediction`. |
| `vertices_list` | List of `(V, 3)` tensors | Usually float tensors. |
| `faces_list` | List of `(F, face_size)` tensors | Dash3D expects triangle meshes for display. |
| `uvs_list`, `face_uvs_idx_list`, `face_normals_list` | Optional mesh attributes | If not repeated at every iteration, USD can reuse authored values. |
| `materials_list` | Optional materials per mesh | Accepts a single `PBRMaterial`, list, or dict of named material variants per mesh. |

Layout written:

```text
log_dir/
  category/
    mesh_0.usd
    mesh_1.usd
    ...
    textures/
      mesh_0_<material>_<iteration>_<channel>.png
```

### `add_pointcloud_batch`

Signature shape:

```python
timelapse.add_pointcloud_batch(
    iteration=0,
    category="",
    pointcloud_list=None,
    colors=None,
    points_type="point_instancer",
)
```

Expected inputs and outputs:

| Argument | Meaning | Notes |
|---|---|---|
| `pointcloud_list` | List of point tensors, each `(N, 3)` | Batch length must match `colors` when colors are supplied. |
| `colors` | Optional list of RGB color tensors | USD writer supports colors for point clouds, but Dash3D does not display point colors. |
| `points_type` | USD representation | Must be `"point_instancer"` or `"usd_geom_points"`; invalid values raise `ValueError`. |

Layout written:

```text
log_dir/
  category/
    pointcloud_0.usd
    pointcloud_1.usd
    ...
```

### `add_voxelgrid_batch`

Signature shape:

```python
timelapse.add_voxelgrid_batch(
    iteration=0,
    category="",
    voxelgrid_list=None,
    colors=None,
    semantic_ids=None,
)
```

Expected inputs and outputs:

| Argument | Meaning | Notes |
|---|---|---|
| `voxelgrid_list` | List of voxel grid tensors | Usually boolean occupancy grids. |
| `colors`, `semantic_ids` | Reserved optional attributes | The inspected implementation raises `NotImplementedError` if either is non-`None`. |

Layout written:

```text
log_dir/
  category/
    voxelgrid_0.usd
    voxelgrid_1.usd
    ...
```

Dash3D does not display voxel grids, although `TimelapseParser` can index them.

## TimelapseParser

Constructor:

```python
parser = kaolin.visualize.TimelapseParser(log_dir)
```

Supported file stems: `mesh_*.usd`, `pointcloud_*.usd`, `voxelgrid_*.usd`.

The parser scans recursively under `log_dir` and builds:

```python
parser.filepaths[(type_str, category, id)] -> file_path
parser.dir_info[type_str] -> [{"category": str, "ids": [int, ...], "end_time": number}, ...]
```

Useful methods:

| Method | Use |
|---|---|
| `get_file_path(type, category, id)` | Get the USD path for `type` in `{"mesh", "pointcloud", "voxelgrid"}`. Returns `None` if absent. |
| `check_for_updates()` | Rescan and return `True` when file paths or modification timestamps changed. |
| `num_mesh_items()`, `num_pointcloud_items()`, `num_voxelgrid_items()` | Count indexed items across categories. |
| `num_mesh_categories()`, `num_pointcloud_categories()`, `num_voxelgrid_categories()` | Count categories by type. |
| `get_category_info(type, category)` | Return `{"category", "ids", "end_time"}` for one category or `None`. |

## Jupyter/IPython visualization APIs

### `quick_viz`

Verified signature:

```python
kaolin.visualize.quick_viz(imgs, nrow=None, inches=15)
```

Behavior:

- Displays a tensor image batch using Matplotlib and returns a `matplotlib.axes.Axes` object.
- Accepts `(B, C, H, W)` or `(C, H, W)` tensors.
- `C` must be `1`, `3`, or `4`; values are expected in `[0, 1]`.
- If `matplotlib` is missing or the tensor shape is unsupported, it warns and returns `None`.
- `nrow=None` means all images in one row; `nrow` is clamped to the batch size.

### Interactive visualizer contract

The interactive visualizers connect a mutable `kaolin.render.camera.Camera` to a user-provided render function.

Render callable contract:

```python
def render(camera):
    # Return either a uint8 image tensor or a dict containing key "img".
    return torch_uint8_hwc_image
    # or
    return {"img": torch_uint8_hwc_image, "extra_debug_value": other_tensor_or_value}
```

Image contract:

- Display image must be a `torch.Tensor` with dtype `torch.uint8` and shape `(H, W, C)`.
- `C=3` is typical; alpha is possible when the renderer provides it.
- The visualizer can display at a canvas resolution different from the render output resolution.

Common constructor arguments:

| Argument | Meaning |
|---|---|
| `height`, `width` | Canvas dimensions. |
| `camera` | Single camera object. The visualizer mutates this camera. Use `copy.deepcopy(camera)` to keep an original. |
| `render` | Full-quality callable used for `.show()` and settled updates. |
| `fast_render` | Optional faster callable used during mouse/key movement. Use lower resolution to avoid UI stalls. |
| `max_fps` | Throttle for event handling; lower it for slow renderers or remote notebooks. |
| `canvas`, `event_canvas` | Optional custom `ipycanvas`/widget event surfaces. |
| `img_format`, `img_quality` | Canvas transfer format. JPEG with lower quality can reduce latency. |
| `additional_watched_events`, `additional_event_handler` | Add keyboard or custom widget controls. Return `False` from the handler to stop default processing. |

### `IpyTurntableVisualizer`

Use for inspecting a small object around a focus point.

Important controls and arguments:

| Feature | Default or behavior |
|---|---|
| Left mouse drag | Rotate around `focus_at`. |
| Mouse wheel | Zoom by changing field of view. |
| Ctrl + mouse wheel | Move closer/farther while preserving turntable orientation. |
| `focus_at` | Defaults to origin. |
| `world_up_axis` | Defaults to `1` (Y axis). |
| `zoom_sensitivity`, `forward_sensitivity`, `rotation_sensitivity`, `translation_sensitivity` | Tune interaction speed. |
| `update_only_on_release` | If `True`, avoid continuous full updates while dragging. |

### `IpyFirstPersonVisualizer`

Use for scenes or detailed inspection where the camera moves through space.

Important controls and arguments:

| Feature | Default or behavior |
|---|---|
| Left mouse drag | Change orientation. |
| Right mouse drag | Translate camera in the view plane. |
| Mouse wheel | Zoom by changing field of view. |
| Keys | Defaults: `i` up, `k` down, `j` left, `l` right, `o` forward, `u` backward. |
| `world_up` | Optional tensor to constrain orientation. |
| `key_move_sensitivity`, `rotation_sensitivity`, `translation_sensitivity`, `zoom_sensitivity` | Tune interaction speed. |

## Canvas update helper

`kaolin.visualize.update_canvas(canvas, image, format="PNG", quality=100)` updates an `ipycanvas.Canvas` with a uint8 `(H, W, C)` tensor. PNG is efficient for exact RGB/RGBA transfer; JPEG can reduce latency at the cost of compression artifacts.

## Dash3D APIs and CLI

Module functions:

```python
from kaolin.experimental.dash3d.run import create_server, run_main
server = create_server(logdir)
```

Verified signatures and parser facts:

| API | Behavior |
|---|---|
| `create_server(logdir)` | Returns a Tornado `Application` backed by Flask routes and websocket geometry streaming. It does not call `listen()` or start the IOLoop. |
| `run_main()` | Parses CLI arguments, creates the server, calls `listen(port)`, and starts `IOLoop.instance().start()` indefinitely. Do not call directly in tests without a process timeout. |
| `--logdir` | Required. Must point to the Timelapse root directory. |
| `--port` | Default `8080`. Choose an unused local port. |
| `--log_level` | Default integer `20` (`INFO`). Common values: `10` DEBUG, `20` INFO, `30` WARN, `40` ERROR. |

Launch command:

```bash
kaolin-dash3d --logdir=./timelapse-logdir --port=8080 --log_level=20
```

Alternative module launch when the script entry point is unavailable:

```bash
python -m kaolin.experimental.dash3d.run --logdir=./timelapse-logdir --port=8080 --log_level=20
```

Dash3D support limits:

- Displays triangle meshes and point clouds.
- Does not display mesh textures, vertex colors, point colors, voxel grids, or semantic IDs.
- Uses a browser/WebGL client and a websocket endpoint.
- The URL query parameter `maxviews` is clamped to 1 through 8, with default 3.

## GLTF interactive visualization composition

This sub-skill only covers the visualization composition. Use geometry/IO references for GLTF import details and rendering references for camera, lighting, and backend issues.

Typical composition:

1. Load a GLTF mesh into a Kaolin mesh container.
2. Normalize/center if desired.
3. Move mesh and camera to the backend required by the renderer.
4. Build a render callable `render(camera)` returning `{"img": uint8_hwc, ...}`.
5. Provide a lower-resolution `fast_render(camera)` if the full renderer is slow.
6. Create `IpyTurntableVisualizer(..., render, fast_render=..., img_format="jpeg", img_quality=75)`.
7. Add `ipywidgets` sliders or keyboard event handlers for lighting/material toggles.
