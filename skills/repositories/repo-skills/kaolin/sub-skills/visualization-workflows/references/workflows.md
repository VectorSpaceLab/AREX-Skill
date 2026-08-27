# Kaolin visualization workflows

Use these workflows to solve common visualization tasks without reopening repository examples.

## Workflow 1: Add Timelapse checkpoints to a training loop

Use when a user has batches of meshes, point clouds, or voxel grids and wants visual checkpoints during training.

### Preconditions

- The task already has geometry tensors. If not, route tensor generation, OBJ/GLTF/USD import, sampling, or conversion to the appropriate geometry/ops owner.
- The environment can import Kaolin and OpenUSD `pxr`.
- The chosen `viz_log_dir` is dedicated to visualization files, not mixed with optimizer checkpoints or configs.

### Pattern

```python
import os
import kaolin

viz_log_dir = "./viz"  # choose a dedicated directory
os.makedirs(viz_log_dir, exist_ok=True)

writer = kaolin.visualize.Timelapse(viz_log_dir)

# Static reference data: write once at iteration 0.
writer.add_mesh_batch(
    category="ground_truth",
    vertices_list=gt_vertices_list,  # list of (V, 3) tensors
    faces_list=faces_list,           # list of (F, 3) or (F, face_size) tensors
)
writer.add_pointcloud_batch(
    category="input",
    pointcloud_list=input_pointcloud_list,
)

for iteration in range(num_iterations):
    # ... user training/update code here ...
    if iteration % checkpoint_interval == 0:
        writer.add_mesh_batch(
            iteration=iteration,
            category="prediction",
            vertices_list=pred_vertices_list,
            faces_list=faces_list,
        )
        writer.add_pointcloud_batch(
            iteration=iteration,
            category="prediction",
            pointcloud_list=pred_pointcloud_list,
        )
```

### Decisions

| Decision | Guidance |
|---|---|
| Category names | Use semantic names such as `input`, `ground_truth`, `prediction`, `output`, `ablation_a`. Category names become directory names. |
| Static vs time-varying | Write static data once. For time-varying meshes with fixed topology, avoid reauthoring unchanged data when practical. |
| Multiple batches | Timelapse assumes one batch per type/category. Use a new category if a second independent batch is needed. |
| Point cloud storage | Use default `points_type="point_instancer"` unless a USD Points representation is explicitly needed. |
| Voxel grids | Timelapse can write them; Dash3D will not display them. |
| Materials | Mesh materials can be logged with `PBRMaterial`; Dash3D will not show those textures/materials. |

## Workflow 2: Verify a Timelapse logdir before launching a UI

Use when automation must determine whether a visualization directory is plausible.

### Fast filesystem check, no Kaolin import

```bash
python scripts/kaolin_dash3d_help.py --logdir ./viz --inspect-logdir
```

The helper reports counts of files matching `mesh_*.usd`, `pointcloud_*.usd`, and `voxelgrid_*.usd`, plus a safe launch command. A directory with only voxel grids is valid Timelapse output but not useful for Dash3D.

### Parser check, requires Kaolin and `pxr`

```python
import kaolin

parser = kaolin.visualize.TimelapseParser("./viz")
print(parser.dir_info)
print("meshes", parser.num_mesh_items())
print("pointclouds", parser.num_pointcloud_items())
print("voxelgrids", parser.num_voxelgrid_items())

# Later, after more checkpoints are written:
if parser.check_for_updates():
    print("visualization directory changed")
```

Expected layout:

```text
viz/
  ground_truth/
    mesh_0.usd
    mesh_1.usd
    textures/
  input/
    pointcloud_0.usd
    pointcloud_1.usd
  prediction/
    mesh_0.usd
    pointcloud_0.usd
    voxelgrid_0.usd
```

## Workflow 3: Start Dash3D safely

Use Dash3D when a user has a Timelapse logdir and wants a lightweight browser-based viewer.

### Safe dry run

```bash
python scripts/kaolin_dash3d_help.py \
  --logdir ./viz \
  --port 8080 \
  --log_level 20 \
  --inspect-logdir
```

### Human-supervised launch

```bash
kaolin-dash3d --logdir=./viz --port=8080 --log_level=20
```

Then open:

```text
http://localhost:8080/
```

For a remote machine, keep the server on the machine with the logdir and use SSH port forwarding from the client. Example pattern:

```bash
ssh -L 8080:localhost:8080 user@remote-host
```

Then open `http://localhost:8080/` on the client.

### Automation rules

- Do not call `run_main()` inside the current Python process for verification; it starts a persistent IOLoop.
- If a test must launch the server, use a subprocess, a unique port, a startup timeout, and cleanup/kill logic.
- Prefer `create_server(logdir)` for unit-level import/parser checks because it returns an application object without starting the IOLoop.
- Use integer log levels: DEBUG `10`, INFO `20`, WARN `30`, ERROR `40`.

### Dash3D capability filter

Before promising Dash3D support, check the requested data against the supported display types.

| Timelapse data | Dash3D display status |
|---|---|
| Triangle meshes | Supported. |
| Point clouds | Supported, positions only. |
| Mesh textures/materials | Not displayed. |
| Vertex colors / point colors | Not displayed. |
| Voxel grids | Not displayed. |
| Semantic IDs | Not displayed. |

## Workflow 4: Quick image grid in scripts or notebooks

Use `quick_viz` for rendered image batches, debug passes, masks, or any tensor image in channels-first format.

```python
import torch
import kaolin

imgs = torch.rand(6, 3, 64, 64)  # values in [0, 1]
ax = kaolin.visualize.quick_viz(imgs, nrow=3, inches=5)
if ax is None:
    print("quick_viz could not display; check matplotlib and tensor shape")
else:
    ax.figure.savefig("debug_grid.png")
```

Shape rules:

- Good: `(B, 1, H, W)`, `(B, 3, H, W)`, `(B, 4, H, W)`, `(C, H, W)` with `C` in `{1, 3, 4}`.
- Bad: HWC tensors, channels other than 1/3/4, non-image rank. Convert before calling.

## Workflow 5: Create a Jupyter turntable visualizer for a custom renderer

Use when a user already has a render function or a rendering owner provides one.

### Minimal notebook cell

```python
import copy
import torch
import kaolin as kal

# camera must be a single Kaolin camera.
camera = kal.render.camera.Camera.from_args(
    eye=torch.tensor([2.0, 1.0, 1.0], device="cuda"),
    at=torch.tensor([0.0, 0.0, 0.0], device="cuda"),
    up=torch.tensor([0.0, 1.0, 0.0], device="cuda"),
    fov=45 * 3.14159265 / 180,
    width=512,
    height=512,
    device="cuda",
)

def render(camera):
    # Replace this with the user's renderer.
    # It must return uint8 HWC or {"img": uint8 HWC, ...}.
    img = torch.zeros((512, 512, 3), dtype=torch.uint8, device=camera.device)
    return {"img": img}

def fast_render(camera):
    # Lower resolution is enough during mouse movement.
    low = copy.deepcopy(camera)
    low.width = camera.width // 4
    low.height = camera.height // 4
    out = render(low)
    return out

visualizer = kal.visualize.IpyTurntableVisualizer(
    512,
    512,
    copy.deepcopy(camera),
    render,
    fast_render=fast_render,
    max_fps=24,
    world_up_axis=1,
)
visualizer.show()
```

### Interaction notes

- Left-drag rotates around `focus_at`.
- Wheel changes field of view.
- Ctrl+wheel moves closer/farther around the focus point.
- Use `update_only_on_release=True` or a low-resolution `fast_render` if the notebook freezes.
- The visualizer mutates its camera. Use `copy.deepcopy(camera)` if the original camera must be preserved.

## Workflow 6: Create a first-person visualizer

Use for large scenes where orbiting around one focus point is less useful.

```python
visualizer = kal.visualize.IpyFirstPersonVisualizer(
    512,
    512,
    copy.deepcopy(camera),
    render,
    fast_render=fast_render,
    max_fps=24,
    world_up=torch.tensor([0.0, 1.0, 0.0], device=camera.device),
    update_only_on_release=False,
)
visualizer.show()
```

Default controls:

| Control | Action |
|---|---|
| Left mouse drag | Rotate view. |
| Right mouse drag | Translate in the view plane. |
| Mouse wheel | Zoom by field of view. |
| `i`, `k` | Move up/down. |
| `j`, `l` | Move left/right. |
| `o`, `u` | Move forward/backward. |

## Workflow 7: Add widgets or custom key events

Use an additional handler to update renderer parameters, toggle passes, or connect sliders.

```python
from ipywidgets import FloatSlider, HBox

exposure = 1.0

def additional_event_handler(visualizer, event):
    with visualizer.out:
        if event["type"] == "keydown" and event.get("key") == " ":
            print("space pressed; toggling debug mode")
            visualizer.render_update()
            return False  # skip default handling for this event
    return True

visualizer = kal.visualize.IpyTurntableVisualizer(
    512,
    512,
    copy.deepcopy(camera),
    render,
    fast_render=fast_render,
    additional_watched_events=["keydown"],
    additional_event_handler=additional_event_handler,
)

slider = FloatSlider(value=1.0, min=0.1, max=4.0, step=0.1, description="Exposure")

def on_slider(change):
    global exposure
    with visualizer.out:
        exposure = change["new"]
        visualizer.render_update()

slider.observe(on_slider, names="value")
visualizer.show()
HBox([slider, visualizer.out])
```

## Workflow 8: Compose an interactive GLTF visualizer

Use when a user wants to inspect a GLTF asset interactively in a notebook. This workflow assumes geometry import and render backend details are already acceptable.

```python
import copy
import torch
import kaolin as kal

mesh = kal.io.gltf.import_mesh("asset.gltf")
mesh = mesh.cuda()
mesh.vertices = kal.ops.pointcloud.center_points(
    mesh.vertices.unsqueeze(0), normalize=True
).squeeze(0)

camera = kal.render.easy_render.default_camera(512).cuda()

azimuth = torch.zeros((1,), device="cuda")
elevation = torch.full((1,), 3.14159265 / 3.0, device="cuda")
amplitude = torch.full((1, 3), 3.0, device="cuda")
sharpness = torch.full((1,), 5.0, device="cuda")

def current_lighting():
    direction = kal.render.lighting.sg_direction_from_azimuth_elevation(azimuth, elevation)
    return kal.render.lighting.SgLightingParameters(
        amplitude=amplitude,
        sharpness=sharpness,
        direction=direction,
    )

def render(camera):
    result = kal.render.easy_render.render_mesh(camera, mesh, lighting=current_lighting())
    img = result[kal.render.easy_render.RenderPass.render]
    normals = result[kal.render.easy_render.RenderPass.normals][0]
    return {
        "img": (torch.clamp(img, 0.0, 1.0)[0] * 255).to(torch.uint8),
        "normals": normals,
    }

def lowres_render(camera):
    low = copy.deepcopy(camera)
    low.width = camera.width // 8
    low.height = camera.height // 8
    return render(low)

visualizer = kal.visualize.IpyTurntableVisualizer(
    512,
    512,
    copy.deepcopy(camera),
    render,
    fast_render=lowres_render,
    max_fps=5,
    world_up_axis=1,
    img_format="jpeg",
    img_quality=75,
)
visualizer.show()
```

Boundary reminders:

- If `import_mesh("asset.gltf")` fails, route to geometry/IO troubleshooting.
- If `render_mesh` fails due to CUDA, nvdiffrast, camera, lighting, or material issues, route to rendering/cameras/lighting troubleshooting.
- If the notebook UI fails to display or handle events, stay in this sub-skill and use the troubleshooting reference.

## Workflow 9: Bounded verification plan for a visualization request

Use this checklist before marking a visualization task complete.

1. `python scripts/kaolin_dash3d_help.py --help` works from any current directory.
2. If Timelapse is involved, inspect layout without starting a server:
   ```bash
   python scripts/kaolin_dash3d_help.py --logdir ./viz --inspect-logdir
   ```
3. If dependencies are in scope, run a safe import probe:
   ```bash
   python scripts/kaolin_dash3d_help.py --check-imports
   ```
4. For Timelapse parser validation, import Kaolin and `pxr`, instantiate `TimelapseParser`, and print `dir_info`.
5. For Dash3D, provide the exact command and browser URL; launch only with human supervision or a subprocess timeout.
6. For Jupyter, confirm that code is intended to run in a Jupyter/IPython display context and document widget/browser dependencies.
