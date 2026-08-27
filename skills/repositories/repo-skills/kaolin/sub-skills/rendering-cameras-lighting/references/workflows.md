# Workflows: Kaolin cameras, rays, rendering, lighting

Use these workflows after the input mesh/data owner has produced the needed tensors or `SurfaceMesh`. Do not use this sub-skill to load or repair mesh files; route that to the geometry/IO owner.

## 1. Build a render-ready camera

Use `Camera.from_args` unless you need explicit `CameraExtrinsics` / `CameraIntrinsics` objects.

```python
import math
import torch
from kaolin.render.camera import Camera

camera = Camera.from_args(
    eye=torch.tensor([1.0, 1.0, 1.0]),
    at=torch.tensor([0.0, 0.0, 0.0]),
    up=torch.tensor([0.0, 1.0, 0.0]),
    fov=math.radians(45.0),
    width=512,
    height=512,
    near=1e-2,
    far=1e2,
    dtype=torch.float32,
    device="cuda",   # or "cpu" for camera-only work
)
```

Checklist:

- Provide one extrinsics description: `eye`/`at`/`up`, `view_matrix`, or `cam_pos`/`cam_dir`.
- Provide one intrinsics description: `fov` or `focal_x` for pinhole, `fov_distance` for orthographic.
- Use a single `device=` if constructor tensors may come from mixed CPU/CUDA devices.
- Remember that `render_mesh` expects one camera. For camera batches, loop over `for cam in cameras:` or use `camera[i]`.

For a centered normalized scene, the easy default is enough:

```python
from kaolin.render.easy_render import default_camera
camera = default_camera(512).cuda()
```

## 2. Match coordinate systems

Kaolin defaults to right-handed Cartesian world axes with `Y` up and `Z` pointing out of the screen. If an incoming camera or mesh convention uses different axes, update the camera coordinate system before rendering or ray generation.

```python
from kaolin.render.camera import blender_coords

camera.change_coordinate_system(blender_coords())
# ... render or generate rays in this basis ...
camera.reset_coordinate_system()
```

Use this for axis convention changes, not for mesh normalization. If the object is not centered or scaled for the camera, route mesh normalization or transform decisions to the data/geometry owner.

## 3. Generate rays

For pinhole/orthographic ray tasks, use the camera's lens-aware method or the functional helpers.

```python
ray_origins, ray_dirs = camera.generate_rays()
assert ray_origins.shape == (camera.height * camera.width, 3)
assert ray_dirs.shape == (camera.height * camera.width, 3)
```

For lower-resolution ray grids on the same image plane:

```python
from kaolin.render.camera import (
    generate_centered_custom_resolution_pixel_coords,
    generate_pinhole_rays,
)

pixel_grid = generate_centered_custom_resolution_pixel_coords(
    img_width=camera.width,
    img_height=camera.height,
    res_x=128,
    res_y=128,
    device=camera.device,
)
ray_origins, ray_dirs = generate_pinhole_rays(camera, pixel_grid)
```

Rules:

- Ray generation supports one camera at a time; split camera batches.
- Custom pixel grids are a tuple `(pixel_y, pixel_x)` and both tensors must be on `camera.device`.
- Principal point offsets `x0` and `y0` are offsets from the canvas center in Kaolin's pinhole convention.

For a bounded smoke check, run:

```bash
python scripts/camera_smoke.py --help
python scripts/camera_smoke.py --resolution 32 --json
```

## 4. Render an existing `SurfaceMesh` with easy PBR

Use this path when a valid single `SurfaceMesh` is already available and the user wants a composited image or standard passes.

```python
import kaolin as kal
from kaolin.render.easy_render import (
    default_camera,
    default_lighting,
    render_mesh,
    RenderPass,
)

# mesh must already be a kaolin.rep.SurfaceMesh; loading belongs to geometry/IO.
device = "cuda"
mesh = mesh.cuda()
camera = default_camera(512).cuda()
lighting = default_lighting().cuda()

result = render_mesh(camera, mesh, lighting=lighting, backend=None)
image = result[RenderPass.render.name]      # composited RGB, shape 1 x H x W x 3
face_idx = result[RenderPass.face_idx]      # enum key, -1 means background
```

Backend selection:

- `backend=None`: use `nvdiffrast` if installed, otherwise bundled Kaolin CUDA.
- `backend="cuda"`: force bundled Kaolin CUDA kernels; requires Kaolin `_C` extension and CUDA.
- `backend="nvdiffrast"`: force optional `nvdiffrast`; requires CUDA and a context.

Before promising this workflow in a new environment, run:

```bash
python scripts/render_backend_probe.py --json
python scripts/render_backend_probe.py --probe-rasterize --backend auto --json
```

Output interpretation:

- `RenderPass.render.name` is the composited image pass; values are not clamped.
- `RenderPass.face_idx` is the face-index map; use it to detect all-background frames.
- `albedo`, `normals`, `diffuse`, `specular`, `uvs`, and `features` appear only when the renderer can compute them from mesh attributes/materials.
- Do not assume `alpha` or `roughness` is present; check the dict.

## 5. Minimal PBR material and lighting plan

If the mesh lacks useful materials or the user wants a controlled constant material:

```python
from kaolin.render.easy_render import default_material, default_lighting, render_mesh

material = default_material(diffuse_color=(0.8, 0.2, 0.2)).to(camera.device)
# If mesh.material_assignments exists, set it so each face uses material index 0.
result = render_mesh(
    camera,
    mesh,
    lighting=default_lighting().to(camera.device),
    custom_materials=[material],
    custom_material_assignments=mesh.material_assignments,
    backend="cuda",
)
```

When creating custom `PBRMaterial` objects:

- Use scalar value tensors for roughness/metallic/opacity-like fields and RGB tensors for diffuse/specular color fields.
- Texture attributes are 3D tensors. Use `.chw()` or `.hwc()` when diagnosing layout; easy render chooses internally by backend.
- `is_specular_workflow=True` uses specular color/texture. If it is false, the metallic workflow is used.
- Missing UVs mean texture maps cannot be sampled. Easy render may still render with constant colors or defaults.

For custom SG lighting:

```python
import torch
from kaolin.render.lighting import SgLightingParameters, sg_direction_from_azimuth_elevation

azimuth = torch.tensor([2.3], device=camera.device)
elevation = torch.tensor([1.0], device=camera.device)
direction = sg_direction_from_azimuth_elevation(azimuth, elevation)
lighting = SgLightingParameters(amplitude=3.0, direction=direction, sharpness=5.0).to(camera.device)
```

## 6. Low-level rasterization for custom image-space features

Use `kaolin.render.mesh.rasterize` when you already have face vertices in camera/image coordinates and need to interpolate arbitrary per-face per-vertex features.

```python
import kaolin as kal

vertices_camera = camera.extrinsics.transform(mesh.vertices)
vertices_ndc = camera.intrinsics.transform(vertices_camera)

face_vertices_camera = kal.ops.mesh.index_vertices_by_faces(vertices_camera, mesh.faces)
face_vertices_image = kal.ops.mesh.index_vertices_by_faces(vertices_ndc[..., :2], mesh.faces)
face_features = mesh.face_uvs  # or any tensor shaped B x F x 3 x C

image_features, face_idx = kal.render.mesh.rasterize(
    height=camera.height,
    width=camera.width,
    face_vertices_z=face_vertices_camera[..., -1],
    face_vertices_image=face_vertices_image,
    face_features=face_features,
    backend="cuda",
)
```

Rules:

- Inputs are batched: `face_vertices_z` is `(B, F, 3)` and `face_vertices_image` is `(B, F, 3, 2)`.
- `face_features` can be a tensor or a list/tuple of tensors. The output mirrors that structure.
- Backends are `cuda`, `nvdiffrast`, and `nvdiffrast_fwd`. High-level `render_mesh` does not expose `nvdiffrast_fwd`.
- `nvdiffrast` paths prefer float32 and image sizes that satisfy the context's resolution constraints.

## 7. DIB-R soft masks and silhouette-style losses

Use `dibr_rasterization` when the task needs a soft foreground mask in addition to feature interpolation.

```python
face_normals_z = kal.ops.mesh.face_normals(face_vertices_camera, unit=True)[..., -1]
features, soft_mask, face_idx = kal.render.mesh.dibr_rasterization(
    camera.height,
    camera.width,
    face_vertices_z=face_vertices_camera[..., -1],
    face_vertices_image=face_vertices_image,
    face_features=face_features,
    face_normals_z=face_normals_z,
    sigmainv=7000,
    boxlen=0.02,
    knum=30,
    rast_backend="cuda",
)
```

Guidance:

- `face_normals_z >= 0` gates visible faces before mask computation.
- Increase `knum` or `boxlen` if the soft mask misses nearby faces; decrease for speed if the mask is over-broad.
- `dibr_soft_mask` can be used directly when rasterization has already produced `face_idx`.

## 8. Differentiable camera optimization

Use this when optimizing camera pose, focal length, or FOV against an image-space loss.

```python
import torch

camera.requires_grad_(True)
ext_mask, int_mask = camera.gradient_mask("t", "focal_x", "focal_y")
ext_params, int_params = camera.parameters()
ext_params.register_hook(lambda grad: grad * ext_mask.float())
int_params.register_hook(lambda grad: grad * int_mask.float())

optimizer = torch.optim.SGD(camera.parameters(), lr=0.1)
# loss = image_loss(render_mesh(camera, mesh)[RenderPass.render.name], target)
# optimizer.zero_grad(); loss.backward(); optimizer.step()
```

Notes:

- For extrinsics, optimized representations should preserve rigid transforms better than raw matrix parameters.
- Restrict gradients when only position or focal length should move.
- Keep render backend constraints in the optimization plan; low-level CUDA/nvdiffrast renderers still need CUDA.

## 9. Backend triage workflow

1. Run a report-only probe:

   ```bash
   python scripts/render_backend_probe.py --json
   ```

2. If the task requires actual CUDA rasterization, run a tiny rasterize probe:

   ```bash
   python scripts/render_backend_probe.py --probe-rasterize --backend cuda --json
   ```

3. If the task requires optional `nvdiffrast`, run:

   ```bash
   python scripts/render_backend_probe.py --probe-nvdiffrast-context --probe-rasterize --backend nvdiffrast --json
   ```

4. If any probe fails, use [troubleshooting](troubleshooting.md) and do not silently change the backend unless the user's request allowed fallback.
