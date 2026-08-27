# Workflows

These workflows are safe operating patterns for future agents. They assume an
installed Kaolin environment and do not rely on source-checkout paths.

## 1. Inspect environment and a candidate file safely

Use the bundled helper before promising that a file can be read:

```bash
python scripts/mesh_io_probe.py --help
python scripts/mesh_io_probe.py --check-imports --json
python scripts/mesh_io_probe.py --kind mesh ./asset.obj --triangulate
python scripts/mesh_io_probe.py --kind gaussian ./scene.ply --json
python scripts/mesh_io_probe.py --kind usd-paths ./scene.usdc --json
```

The helper imports Kaolin only after argument parsing. `--help` should succeed
even when Kaolin or optional dependencies are missing.

## 2. Load one mesh into `SurfaceMesh`

Start with the generic selector when no fine-grained options are required:

```python
import kaolin as kal

mesh = kal.io.import_mesh("model.obj", triangulate=True)
print(mesh)
assert mesh.check_sanity()
```

Then normalize for downstream owners:

```python
# Apply any stored transform and return a world-space mesh.
mesh_world = mesh.as_transformed()

# Batch a single mesh if a downstream API expects B dimension.
mesh_batched = mesh_world.to_batched()

# Keep only selected tensors on CUDA if the next owner requires GPU.
mesh_gpu_vertices = mesh_world.cuda(attributes=["vertices"])
```

Important decisions:

- `kaolin.io.import_mesh` supports OBJ, USD, GLTF, and GLB. It does not support
  OFF and does not expose USD `scene_path`/`time`.
- Imported tensors are generally CPU tensors until explicitly moved.
- `mesh.face_normals`, `mesh.face_uvs`, and `mesh.face_vertices` may be
  auto-computed lazily. Use `has_attribute` to check explicit fields and
  `get_or_compute_attribute` when you want a controlled cache decision.
- If a downstream renderer or op needs indexed UVs/normals and the mesh only has
  face-varying values, use `mesh.ensure_indexed_attribute("uvs")` or
  `mesh.ensure_indexed_attribute("normals")` before handoff.

## 3. Mixed OBJ / GLTF / USD mesh import plan

When a user provides several mesh files in mixed formats and wants a unified
`SurfaceMesh`:

```python
from kaolin.io import obj, gltf, usd, utils as io_utils
from kaolin.rep import SurfaceMesh

meshes = []

# OBJ: choose material and heterogeneity policy.
meshes.append(obj.import_mesh(
    "asset.obj",
    with_materials=True,
    with_normals=True,
    raw_materials=False,
    error_handler=obj.skip_error_handler,
    heterogeneous_mesh_handler=io_utils.mesh_handler_naive_triangulate,
    triangulate=True,
))

# GLTF: scene composition is performed by import_mesh.
meshes.append(gltf.import_mesh("asset.gltf"))

# USD: use a scene path and time when the stage is organized/animated.
meshes.append(usd.import_mesh(
    "asset.usdc",
    scene_path="/World/Asset",
    time=None,
    with_materials=True,
    with_normals=True,
    heterogeneous_mesh_handler=io_utils.mesh_handler_naive_triangulate,
    triangulate=True,
))

# Remove failed/empty imports and merge in world space.
meshes = [m for m in meshes if m is not None]
combined = SurfaceMesh.flatten(meshes, group_materials_by_name=True)
assert combined.batching == SurfaceMesh.Batching.NONE
assert combined.check_sanity()
```

Pitfalls to surface before coding:

- OBJ direct import defaults to no materials/normals; generic import requests
  them. Be explicit.
- OBJ raw materials are dictionaries; glTF and USD usually return `PBRMaterial`.
  Use `raw_materials=False` if you need a common PBR-like material list.
- Heterogeneous face sizes raise unless you pass `triangulate=True` or a
  `heterogeneous_mesh_handler`. If skipping, downstream material assignments and
  face counts change.
- `SurfaceMesh.cat` creates batches and preserves transforms. `SurfaceMesh.flatten`
  applies transforms and returns one world-space mesh.
- `group_materials_by_name=True` deduplicates same-named materials; use
  `False` when you need to preserve source material slots exactly.
- If a mixed import feeds rendering, route camera/light/shader decisions to
  `rendering-cameras-lighting` after the mesh contract is normalized.

## 4. Construct `SurfaceMesh` from raw tensors

```python
import torch
from kaolin.rep import SurfaceMesh

vertices = torch.tensor([
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
], dtype=torch.float32)
faces = torch.tensor([[0, 1, 2]], dtype=torch.long)

mesh = SurfaceMesh(vertices=vertices, faces=faces, strict_checks=True)
assert mesh.is_triangular()
face_vertices = mesh.get_or_compute_attribute("face_vertices", should_cache=True)
face_normals = mesh.get_or_compute_attribute("face_normals", should_cache=False)
```

For batching:

```python
# Fixed topology: same faces for every mesh.
fixed = SurfaceMesh(vertices=torch.stack([vertices, vertices + 1]), faces=faces)

# Variable topology: lists.
listed = SurfaceMesh(vertices=[vertices, vertices[:2]], faces=[faces, torch.zeros((0, 3), dtype=torch.long)])
```

If strict shape checks fail, print the expected shape table:

```python
print(SurfaceMesh.attribute_info_string(SurfaceMesh.Batching.NONE))
print(mesh.to_string(detailed=True, print_stats=True))
```

## 5. Load and export Gaussian PLY

```python
from kaolin.io import ply

gaussians = ply.import_gaussiancloud("scene.ply")
assert gaussians.check_sanity()
print(gaussians.to_string(print_stats=True))

# Round-trip, preserving optional extra feature dicts.
ply.export_gaussiancloud(
    "roundtrip.ply",
    **gaussians.as_dict(only_tensors=True),
    overwrite=True,
)
```

Before exporting custom features:

```python
features = {"albedo": albedo_tensor, "roughness": roughness_tensor}
# Every feature tensor must be shape (N, K), and names must not collide with
# standard PLY prefixes such as f_dc, f_rest, opacity, scale, rot, x, y, z.
```

If an import fails, use [troubleshooting](troubleshooting.md) to check required
PLY fields and `sh_coeff` square-degree consistency.

## 6. USD Gaussian workflow with scene paths and transforms

```python
import torch
from kaolin.io import usd

N = 4
positions = torch.rand(N, 3)
orientations = torch.nn.functional.normalize(torch.rand(N, 4), dim=-1)
scales = torch.ones(N, 3) * 0.05
opacities = torch.ones(N)
sh_coeff = torch.zeros(N, 16, 3)  # sh_degree=3 because (3+1)^2 = 16
local_to_world = torch.eye(4)
local_to_world[:3, 3] = torch.tensor([1.0, 2.0, 3.0])

usd.export_gaussiancloud(
    "gaussians.usdc",
    scene_path="/World/Gaussians/object_0",
    positions=positions,
    orientations=orientations,
    scales=scales,
    opacities=opacities,
    sh_coeff=sh_coeff,
    local_to_world=local_to_world,
    time=1,
    overwrite=True,
)

# Per-prim local-space import, retaining transform.
per_prim = usd.import_gaussianclouds(
    "gaussians.usdc",
    scene_paths=["/World/Gaussians/object_0"],
    times=[1],
    return_list=False,
)

# Merged world-space import, transform applied.
merged = usd.import_gaussiancloud("gaussians.usdc", scene_path="/World/Gaussians", time=1)
```

Notes:

- `scene_path` must be an absolute USD path.
- `time` is optional; `None` means default time code.
- `orientations` are supplied as `(w,x,y,z)`. The USD writer stores in USD's
  quaternion convention and the reader converts back.
- `sh_coeff.shape[1]` must be a perfect square.
- If multiple clouds have different SH degrees, validate before merging; use
  `GaussianSplatModel.cat(..., skip_errors=True)` only when truncating higher
  bands is acceptable.

## 7. USD point cloud workflow

```python
from kaolin.io import usd

# Write colored points as UsdGeomPoints.
usd.export_pointcloud(
    "points.usda",
    scene_path="/World/PointClouds/colored",
    points=points,          # (N, 3)
    colors=colors,          # (N, 3), only supported for usd_geom_points
    points_type="usd_geom_points",
    overwrite=True,
)

# Import merged world-space points.
cloud = usd.import_pointcloud("points.usda", scene_path="/World/PointClouds")
points_world = cloud.points
```

For point-sample container utilities:

```python
from kaolin.rep import PointSamples
samples = PointSamples(positions=points_world, features={"rgb": cloud.colors} if cloud.colors is not None else None)
```

Route point sampling, nearest-neighbor metrics, and point-cloud conversions to
`ops-metrics-conversions`.

## 8. USD mesh export workflow

```python
from kaolin.io import usd

mesh = mesh.as_transformed()
uvs, face_uvs_idx = mesh.ensure_indexed_attribute("uvs")

usd.export_mesh(
    "mesh.usda",
    scene_path="/World/Meshes/mesh_0",
    vertices=mesh.vertices,
    faces=mesh.faces,
    uvs=uvs,
    face_uvs_idx=face_uvs_idx,
    face_normals=mesh.get_or_compute_attribute("face_normals", should_cache=False),
    material_assignments=mesh.material_assignments,
    materials=mesh.materials,
    local_to_world=None,
    up_axis="Y",
    overwrite=True,
)
```

Export checks:

- `faces` must be homogeneous `(F,FSz)` for each mesh.
- `face_uvs_idx` requires `uvs`.
- `face_normals` should be `(F,FSz,3)`.
- `materials` and `material_assignments` are both required to write material
  subsets.
- Use `overwrite=True` to replace the whole stage; otherwise use `create_stage`,
  `add_mesh`, then `stage.Save()`.

## 9. Dataset wrapper and cache workflow

Prefer dictionary outputs:

```python
from kaolin.io.shapenet import ShapeNetV2
from kaolin.io.dataset import CachedDataset

dataset = ShapeNetV2(
    root="/data/ShapeNetCore.v2",
    categories=["chair"],
    train=True,
    split=0.8,
    with_materials=False,
    output_dict=True,
)

cached = CachedDataset(
    dataset,
    cache_dir="./cache/shapenet_chair",
    save_on_disk=["mesh"],
    num_workers=0,
    force_overwrite=False,
    cache_at_runtime=True,
)
item = cached[0]
mesh = item["mesh"]
```

Cache caveats:

- `CachedDataset` calls `dataset[0]` at construction to validate output keys.
- Items must be dictionaries; legacy namedtuple outputs are incompatible.
- If preprocessing touches CUDA tensors, set `num_workers=0`.
- Existing cache directories with mismatched item counts raise unless
  `force_overwrite=True`.
- If cached `.pt` values differ from fresh values, use `force_overwrite=True` or
  explicitly accept `ignore_diff_error=True`.

## 10. Hand off to other sub-skills

After this sub-skill normalizes data, hand off using concrete contracts:

- `SurfaceMesh` contract: batching strategy, set tensor attributes, material
  mode, transform state, and whether normals/UVs are indexed or face-varying.
- `GaussianSplatModel` contract: `N`, SH degree/coeff count, dtype/device,
  features keys/shapes, transform state, and PLY/USD source.
- `Spc` contract: `octrees` dtype/device, `lengths`, `max_level`, and which
  derived fields are already present; route kernels to `ops-metrics-conversions`.
- Dataset contract: wrapper class, root, split/categories, `output_dict`, cache
  policy, and whether downloads or remote data were intentionally avoided.
