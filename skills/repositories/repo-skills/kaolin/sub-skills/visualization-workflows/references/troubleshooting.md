# Kaolin visualization troubleshooting

Use this reference when a Timelapse, Dash3D, notebook, GLTF visualization, or image-grid task fails. Prefer safe probes before launching servers or browser UI.

## Fast triage table

| Symptom | Likely cause | Safe probe | Fix or next action |
|---|---|---|---|
| `Warning: module pxr not found`, `ModuleNotFoundError: No module named 'pxr'` | OpenUSD Python bindings are missing | `python - <<'PY'\nfrom pxr import Usd\nprint('pxr ok')\nPY` | Install/provision OpenUSD Python bindings compatible with the environment. Timelapse USD parsing/writing and Dash3D USD reading need this. |
| `quick_viz` returns `None` with a warning | Bad tensor shape or missing Matplotlib | Check tensor rank/channels; `python - <<'PY'\nimport matplotlib\nprint('matplotlib ok')\nPY` | Use `(B,C,H,W)` or `(C,H,W)` with `C` in `{1,3,4}` and values in `[0,1]`; install Matplotlib if absent. |
| Import warning from `kaolin.visualize.ipython` mentioning `ipycanvas`, `ipyevents`, or `ipywidgets` | Notebook widget dependencies are absent or incompatible | `python - <<'PY'\nimport ipycanvas, ipyevents, ipywidgets, comm\nprint('widgets ok')\nPY` | Install widget packages and restart the notebook kernel/browser. |
| `.show()` raises `NameError: display` in a script | Running outside IPython/Jupyter display context | `python - <<'PY'\ntry:\n    display\n    print('display exists')\nexcept NameError:\n    print('not an IPython display context')\nPY` | Run in Jupyter/IPython, or do not call `.show()` in headless scripts. Use render functions and image saves for scripts. |
| Dash3D command never returns | Normal behavior: it starts a server IOLoop | N/A | Do not call `run_main()` for dry-run verification. Use `scripts/kaolin_dash3d_help.py` or a subprocess with timeout/cleanup. |
| Dash3D page opens but shows no data | Wrong `--logdir`, no supported `mesh_*.usd`/`pointcloud_*.usd`, voxelgrid-only output, or parser cannot read USD | `python scripts/kaolin_dash3d_help.py --logdir ./viz --inspect-logdir` | Point `--logdir` to the Timelapse root, not a category subdirectory. Ensure triangle meshes or point clouds exist. |
| Dash3D cannot show colors/textures/voxel grids | Dash3D support limit | Inspect counts and requested data types | Use a USD viewer for materials/textures/voxel grids, or explain that Dash3D only displays mesh geometry and point positions. |
| Port already in use | Another service is bound to the selected port | `python - <<'PY'\nimport socket\ns=socket.socket(); print(s.connect_ex(('127.0.0.1', 8080)))\nPY` | Pick another port, e.g. `--port=8081`, and update browser/SSH forwarding. |
| Browser cannot connect to remote Dash3D | Firewall, host binding, missing SSH forwarding, wrong port | Check local tunnel and server logs | Use SSH forwarding: `ssh -L 8080:localhost:8080 user@remote-host`, then open `http://localhost:8080/`. |
| Notebook visualizer freezes while dragging | Full renderer is too slow or remote latency is high | Try a tiny `fast_render` or lower `max_fps` | Provide `fast_render`, set `update_only_on_release=True`, lower canvas size, use JPEG with lower quality. |
| `AssertionError: No attributes provided` in Timelapse | Called a Timelapse add method with all data fields `None` | Inspect call arguments | Pass at least one data list such as `vertices_list`, `pointcloud_list`, or `voxelgrid_list`. |
| `Number of samples for each attribute must be equal` | List arguments in one Timelapse call have different lengths | Print `len()` of each non-`None` list | Pad/split batches or pass consistent per-sample lists. |
| `ValueError` about `points_type` | Unsupported point cloud USD representation | Print the argument | Use `points_type="point_instancer"` or `points_type="usd_geom_points"`. |
| `NotImplementedError` in voxel grid Timelapse call | `colors` or `semantic_ids` supplied for voxel grids | Inspect call | Omit voxel grid `colors` and `semantic_ids`; they are reserved but not implemented in the inspected version. |
| GLTF visualizer fails during import | Geometry/IO issue | Import GLTF separately without visualization | Route to geometry/IO sub-skill. |
| GLTF visualizer fails during `render_mesh` | Renderer, camera, lighting, CUDA, nvdiffrast, or material issue | Run a rendering backend probe | Route to rendering/cameras/lighting sub-skill. |

## Dependency probes

### Minimal all-in-one visualization import probe

```bash
python - <<'PY'
import importlib
mods = [
    'kaolin',
    'pxr.Usd',
    'matplotlib',
    'ipycanvas',
    'ipyevents',
    'ipywidgets',
    'flask',
    'tornado',
]
for mod in mods:
    try:
        importlib.import_module(mod)
        print(f'OK   {mod}')
    except Exception as exc:
        print(f'MISS {mod}: {type(exc).__name__}: {exc}')
PY
```

Interpretation:

- Missing `pxr.Usd`: Timelapse parser/writer and Dash3D USD reads are blocked.
- Missing `matplotlib`: only `quick_viz` is affected.
- Missing `ipycanvas`, `ipyevents`, `ipywidgets`, or `comm`: notebook interactive visualizers are affected.
- Missing `flask` or `tornado`: Dash3D server is blocked.

### Dash3D-safe helper probe

```bash
python scripts/kaolin_dash3d_help.py --check-imports
python scripts/kaolin_dash3d_help.py --logdir ./viz --inspect-logdir
```

The helper intentionally avoids importing Kaolin unless `--check-imports` is requested and intentionally avoids starting a server.

## Timelapse troubleshooting details

### Use the correct log root

`--logdir` and `TimelapseParser(log_dir)` must receive the Timelapse root, not a category subdirectory.

Good:

```text
viz/
  input/pointcloud_0.usd
  output/mesh_0.usd
```

Use `--logdir=viz`.

Bad:

```text
viz/output/mesh_0.usd
```

Do not use `--logdir=viz/output` unless `output` itself is a complete Timelapse root for another run.

### Category/file naming conventions

The parser indexes files by basename pattern:

```text
mesh_<id>.usd
pointcloud_<id>.usd
voxelgrid_<id>.usd
```

Files with other basenames may be ignored or logged as malformed. Category is derived from the path relative to the log root.

### Static and time-varying data

- Fixed data can be written once with default `iteration=0`.
- Time-varying data should be written with increasing `iteration` values.
- If mesh topology is fixed, avoid rewriting faces/materials when only vertices change, when the surrounding workflow allows it.
- `TimelapseParser` uses authored USD time samples to compute `end_time`; stale or invalid USD files can produce misleading metadata.

### Materials and textures

- Mesh `materials_list` can author material variants and texture PNGs under `textures/`.
- Use a full USD viewer for materials/textures. Dash3D does not display them.
- If texture files are missing, inspect the material object and the output directory write permissions.

## Dash3D troubleshooting details

### Do not accidentally start an endless server in tests

Unsafe for ordinary validation:

```python
from kaolin.experimental.dash3d.run import run_main
run_main()  # parses argv and starts IOLoop indefinitely
```

Safer alternatives:

```python
from kaolin.experimental.dash3d.run import create_server
server = create_server("./viz")  # does not listen or start IOLoop
print(server)
```

or:

```bash
python scripts/kaolin_dash3d_help.py --logdir ./viz --inspect-logdir
```

If an integration test must launch Dash3D, use a subprocess, wait for startup with a timeout, then terminate it. Never leave it running in a shared automation session.

### CLI argument reminders

```bash
kaolin-dash3d --logdir=./viz --port=8080 --log_level=20
```

- `--logdir` is required.
- `--port` defaults to `8080`; pick an unused port.
- `--log_level` is an integer. Use `10` DEBUG when diagnosing parser/websocket behavior.

### Empty or partial UI

Check in order:

1. Does the directory contain `mesh_*.usd` or `pointcloud_*.usd` below category directories?
2. Is `--logdir` the Timelapse root?
3. Can `pxr.Usd` open the files?
4. Are the meshes triangulated? Dash3D expects triangle meshes.
5. Is the browser WebGL-capable and allowed to run JavaScript?
6. Is the websocket endpoint reachable through the same host/port as the page?
7. Is the URL limiting views? `maxviews` is clamped to 1 through 8.

## Jupyter/IPython troubleshooting details

### Widget installation and kernel state

The Python environment and the active Jupyter kernel must use the same packages. After installing widget packages, restart the kernel and browser tab.

Required/common packages:

```text
ipycanvas
ipyevents
ipywidgets
comm
jupyter_client
```

### Render function contract failures

The visualizer expects either:

```python
return image_uint8_hwc
```

or:

```python
return {"img": image_uint8_hwc, "debug": extra_value}
```

Common mistakes:

- Returning float images in `[0, 1]` instead of `torch.uint8`.
- Returning channels-first `(C, H, W)` instead of HWC.
- Returning a dict without key `"img"`.
- Returning a tuple from full `render`; tuple handling is only tolerated for some `fast_render` paths.
- Running CUDA rendering in a CPU-only kernel.

Safe conversion pattern:

```python
img = torch.clamp(img_float, 0.0, 1.0)
img = (img[0] * 255).to(torch.uint8)  # if img was batched BHWC
return {"img": img}
```

### UI latency reductions

Try these in order:

1. Lower canvas dimensions.
2. Provide `fast_render` with a copied low-resolution camera.
3. Set `max_fps` lower, e.g. `5` or `10`.
4. Set `update_only_on_release=True`.
5. Use `img_format="jpeg"` and `img_quality=75`.
6. Reduce extra debug tensors in the returned dict.

## GLTF visualization troubleshooting boundaries

Stay in this sub-skill for UI composition and notebook issues. Route these failures elsewhere:

- GLTF file cannot be parsed, materials are missing, tensor container is unexpected: geometry/IO.
- Camera, lighting, `easy_render.render_mesh`, rasterization, CUDA, or nvdiffrast failure: rendering/cameras/lighting.
- Mesh normalization, sampling, conversion to point cloud/voxel grid: ops/metrics/conversions.

A safe isolation sequence:

```python
# 1. Geometry-only import.
mesh = kal.io.gltf.import_mesh("asset.gltf")
print(mesh)

# 2. Renderer-only smoke with a tiny/default camera, handled by rendering owner if it fails.
# 3. Visualization-only check with a dummy uint8 image renderer.
def dummy_render(camera):
    import torch
    return {"img": torch.zeros((64, 64, 3), dtype=torch.uint8, device=camera.device)}
```

If dummy visualization works but GLTF rendering fails, the visualizer is not the root cause.
