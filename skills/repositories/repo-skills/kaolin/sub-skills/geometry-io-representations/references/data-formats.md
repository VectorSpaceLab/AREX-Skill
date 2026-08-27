# Data formats and selector rules

Use this reference to choose the right Kaolin importer/exporter and understand
format-specific caveats. For signatures, see [API reference](api-reference.md).

## Selector overview

| User artifact | Preferred API | Notes |
|---|---|---|
| `.obj` mesh | `kaolin.io.import_mesh(path)` for quick load; `kaolin.io.obj.import_mesh(...)` for material/normals/error policy | Generic selector loads materials/normals and can triangulate via `triangulate=True`; direct OBJ importer exposes `raw_materials` and handlers. |
| `.gltf` / `.glb` mesh | `kaolin.io.import_mesh(path)` or `kaolin.io.gltf.import_mesh(path, scene=None)` | glTF importer composes selected scene transforms into one `SurfaceMesh`; `import_meshes` returns uncomposed mesh list. |
| `.usd` / `.usda` / `.usdc` / `.usdz` mesh | `kaolin.io.import_mesh(path)` for merged mesh; `kaolin.io.usd.import_mesh(es)` for scene paths/times/materials | Requires `pxr`; direct API handles `scene_path`, `time`, materials, normals, heterogeneous handlers, and multiple mesh returns. |
| `.off` mesh | `kaolin.io.off.import_mesh(path, with_face_colors=False)` | Returns namedtuple, not `SurfaceMesh`; convert manually if a SurfaceMesh is required. |
| 3DGS `.ply` Gaussian splat | `kaolin.io.import_gaussiancloud(path)` or `kaolin.io.ply.import_gaussiancloud(path)` | PLY importer expects standard 3D Gaussian Splat fields; not a general PLY mesh reader. |
| USD Gaussian splat | `kaolin.io.import_gaussiancloud(path)` or `kaolin.io.usd.import_gaussiancloud(es)` | Requires `pxr`; USD prim type is `ParticleField3DGaussianSplat`. |
| USD point cloud | `kaolin.io.usd.import_pointcloud(es)` | Returns namedtuple(s), not `PointSamples`; can be wrapped manually in `PointSamples`. |
| ShapeNet/ModelNet/SHREC dataset root | `ShapeNetV1`, `ShapeNetV2`, `ModelNet`, `SHREC16` | Prefer `output_dict=True` if caching or transforms expect dictionaries. |

There is no generic mesh exporter in this API surface. USD exports are provided
for meshes, point clouds, and Gaussian splats. PLY export is provided for
Gaussian splats. OBJ/OFF/GLTF exports are not exposed by these Kaolin I/O
functions.

## OBJ mesh details

Direct OBJ import:

```python
from kaolin.io import obj
from kaolin.io import utils as io_utils

mesh = obj.import_mesh(
    "model.obj",
    with_materials=True,
    with_normals=True,
    error_handler=obj.skip_error_handler,
    heterogeneous_mesh_handler=io_utils.mesh_handler_naive_triangulate,
    triangulate=True,
    raw_materials=False,
)
```

Operational facts:

- Returns an unbatched CPU `SurfaceMesh`.
- OBJ face indices become zero-based `faces` tensors.
- `with_materials=True` loads UVs, `face_uvs_idx`, `materials`, and
  `material_assignments`; without it these are unset/`None`.
- `with_normals=True` loads `normals` and `face_normals_idx`; otherwise
  `face_normals` can be auto-computed only for triangular faces from geometry.
- `triangulate=True` applies naive polygon triangulation. If a custom
  `heterogeneous_mesh_handler` is supplied, it runs first; triangulation runs
  after that if needed.
- `raw_materials=True` returns raw MTL dictionaries. `raw_materials=False`
  converts supported fields to `PBRMaterial`.
- `material_assignments` is a short/int tensor of length `num_faces`; values
  index the sorted material list, with `-1` for unassigned faces.

Common handlers:

- `obj.default_error_handler`: raise material/parser errors.
- `obj.skip_error_handler`: warn and skip material errors.
- `obj.ignore_error_handler`: ignore errors.
- `obj.create_missing_materials_error_handler`: create dummy materials for
  missing `usemtl` references and warn for file/load errors.

## OFF mesh details

```python
from kaolin.io import off
out = off.import_mesh("model.off", with_face_colors=True)
vertices, faces, face_colors = out.vertices, out.faces, out.face_colors
```

OFF import returns a namedtuple with:

- `vertices`: `(V,3)` float tensor.
- `faces`: `(F,FSz)` long tensor.
- `face_colors`: `(F,3)` long tensor in `[0,255]` when requested, else `None`.

If downstream code needs `SurfaceMesh`, construct one manually:

```python
from kaolin.rep import SurfaceMesh
mesh = SurfaceMesh(vertices=out.vertices, faces=out.faces)
```

Face colors from OFF are per face, not per-face-per-vertex floating colors;
normalize and tile them deliberately before storing in `SurfaceMesh.face_colors`.

## GLTF / GLB mesh details

```python
from kaolin.io import gltf
mesh = gltf.import_mesh("asset.gltf", scene=None)
meshes = gltf.import_meshes("asset.gltf")
```

Operational facts:

- `import_mesh` loads the default glTF scene unless `scene` is specified.
- Node transforms are applied to vertices, tangents, and normals before
  flattening scene meshes into one `SurfaceMesh`.
- `import_meshes` returns individual mesh objects without scene composition.
- Materials are converted to `PBRMaterial`, including metallic/roughness,
  specular-glossiness, normal textures, and some transmission extension values.
- UVs use `face_uvs_idx = faces` when available.
- Unsupported or partial features can warn rather than fail: non-triangle
  primitive modes, vertex colors, vertex skinning, and unsupported sampler
  wrapping modes.

## USD conventions

USD APIs accept either a file path or an open `Usd.Stage` object. When writing
new files, the stage helpers create `/World` and default scene paths such as:

- Mesh: `/World/Meshes/mesh_0`
- Point cloud: `/World/PointClouds/pointcloud_0`
- Gaussian splat: `/World/Gaussians/gaussian_0`

Scene paths must be absolute USD paths. Prefix filters such as
`scene_path="/World/Foo"` select only prims under that subtree.

### Stage and time

- `time=None` means default USD time code.
- APIs that accept `times` broadcast a scalar `time` or require one value per
  `scene_path`.
- `get_authored_time_samples(stage_or_path)` can discover authored samples.
- `create_stage(file_path, up_axis='Y')` expects the output directory to exist
  and supports up axes used by the API (`Y` and `Z` in mesh docs; point/Gaussian
  helpers also accept `X` in some signatures).

### Transform convention

Kaolin returns local-to-world transforms as PyTorch `(4,4)` matrices with
translation in the **last column**. USD stores matrices in its own row-major
convention; the helper transposes when reading/writing.

- `get_local_to_world_transform(...)` returns `None` for identity transforms.
- `set_local_to_world_transform(...)` writes a local transform so the prim's
  computed world transform equals the supplied Kaolin matrix, accounting for
  parent transforms.
- `SurfaceMesh.as_transformed()` and `SurfaceMesh.flatten(...)` apply stored
  transforms and clear them.
- `usd.import_mesh(...)` returns one merged world-space `SurfaceMesh`.
- `usd.import_meshes(...)` returns per-prim local-space meshes with optional
  `transform` fields.
- `usd.import_gaussiancloud(...)` merges and applies transforms.
- `usd.import_gaussianclouds(...)` returns per-prim `GaussianSplatModel` values
  with optional stored `transform`.
- `usd.import_pointcloud(...)` merges and applies transforms.
- `usd.import_pointclouds(...)` returns local-space namedtuples with optional
  transform.

### USD mesh

USD mesh import supports homogeneous meshes directly and heterogeneous meshes
through handlers:

```python
from kaolin.io import usd, utils as io_utils
mesh = usd.import_mesh(
    "scene.usdc",
    scene_path="/World/Asset",
    with_materials=True,
    with_normals=True,
    heterogeneous_mesh_handler=io_utils.mesh_handler_naive_triangulate,
    triangulate=True,
)
```

Operational facts:

- `get_mesh_scene_paths(file_or_stage, scene_path=None)` discovers mesh prims.
- `import_meshes(..., return_list=False)` returns a dict keyed by scene path.
- `import_mesh(...)` merges matching meshes using `SurfaceMesh.flatten`.
- UV interpolation supports `vertex`, `varying`, and `faceVarying`; unsupported
  interpolation raises.
- Face-varying normals are returned as `face_normals`; vertex normals as
  `vertex_normals`.
- Materials are read from bound materials/subsets and converted through the USD
  material manager. Material assignments align with faces.
- Export requires homogeneous `faces` per mesh; heterogeneous source meshes
  should be triangulated or otherwise homogenized before export.
- `overwrite=False` protects whole stage files; use `add_mesh` to mutate an open
  stage and then `stage.Save()`.

### USD point cloud

Kaolin supports `UsdGeom.Points` and `PointInstancer` point clouds.

```python
from kaolin.io import usd
cloud = usd.import_pointcloud("points.usda", scene_path="/World/points")
# cloud.points: (N,3); cloud.colors: (N,3) or None; cloud.transform is None after merge.
```

Operational facts:

- `points_type='point_instancer'` is the default exporter mode.
- Use `points_type='usd_geom_points'` to export display colors.
- Colors must match point shape `(N,3)` and only work for `usd_geom_points`.
- `normals` are currently not implemented and return `None`.
- Older argument names (`pointcloud`, `color`, `pointclouds`) are accepted with
  deprecation warnings; prefer `points` and `colors`.

### USD Gaussian splats

USD Gaussian APIs use `ParticleField3DGaussianSplat` prims.

Required tensors:

- `positions`: `(N,3)` floating tensor.
- `orientations`: `(N,4)` floating tensor in `(w,x,y,z)` convention.
- `scales`: `(N,3)` floating tensor.
- `opacities`: `(N,)` floating tensor; `(N,1)` may be squeezed by `add_gaussiancloud`.
- `sh_coeff`: `(N,(L+1)^2,3)` floating tensor; second dimension must be a
  perfect square.

Operational facts:

- `get_gaussiancloud_scene_paths(...)` discovers Gaussian prim paths.
- `import_gaussianclouds(..., return_list=False)` returns a dict keyed by scene
  path. Each model may have a stored `transform`.
- `import_gaussiancloud(...)` merges matching clouds in world space.
- Half-precision USD attributes may import as half tensors; downstream code
  should not assume float32 unless it casts explicitly.
- `add_gaussiancloud` mutates an open stage and can replace an existing prim
  only with `overwrite=True`.
- `export_gaussiancloud` writes a new stage and requires all standard tensors.

## PLY Gaussian splat schema

Kaolin's PLY reader is for 3D Gaussian Splat clouds, not generic mesh PLY.
The standard vertex properties are:

| Group | Required fields |
|---|---|
| Position | `x`, `y`, `z` |
| Density/opacity | `opacity` |
| SH DC color | `f_dc_0`, `f_dc_1`, `f_dc_2` |
| SH higher bands | zero or more `f_rest_0`, `f_rest_1`, ... fields; count must produce a valid SH degree with DC included |
| Scale | one or more `scale_0`, `scale_1`, ...; practical Gaussian model expects 3 scale values |
| Rotation | `rot_0`, `rot_1`, `rot_2`, `rot_3` for quaternion values |
| Ignored common normals | `nx`, `ny`, `nz` are consumed/ignored as part of standard schema |

`import_gaussiancloud(..., apply_activations=True)` applies:

- `torch.sigmoid` to raw opacity/density.
- `torch.exp` to raw scale.
- quaternion normalization to rotation.

Extra PLY properties are recovered as `GaussianSplatModel.features` only when
they follow `{feature_name}_{integer}`. Columns are sorted by numeric suffix and
feature names may themselves contain underscores. Extra non-indexed properties
are ignored. Export rejects feature keys that collide with reserved standard
prefixes such as `opacity`, `f_dc`, `f_rest`, `scale`, `rot`, `x`, `y`, `z`,
`nx`, `ny`, or `nz`.

## Materials across formats

| Source | Material result | Notes |
|---|---|---|
| OBJ MTL with `raw_materials=True` | raw dicts | Common fields include `Kd`, `Ka`, `Ks`, texture maps, bump/disp/opacity/roughness/metallic-like maps, and `material_name`. |
| OBJ MTL with `raw_materials=False` | `PBRMaterial` | Converts supported fields; unsupported fields warn and are best preserved by using raw mode. |
| glTF | `PBRMaterial` | Metallic/roughness, specular-glossiness, normal textures, and transmission extension fields are mapped when supported. |
| USD | `PBRMaterial` or raw shader params | USD Preview Surface is the registered default reader/writer; unsupported material inputs may warn and be discarded on export. |

When merging meshes, choose one policy:

1. Preserve per-source material lists and remap assignments manually.
2. Use `SurfaceMesh.flatten(meshes, group_materials_by_name=False)` to append
   material lists and offset assignments.
3. Use `group_materials_by_name=True` to deduplicate same-named materials and
   remap assignments.

## Dataset wrapper formats

- `ShapeNetV1` loads `model.obj` under each model directory.
- `ShapeNetV2` loads `models/model_normalized.obj`.
- `ModelNet` loads OFF files and returns OFF namedtuple meshes, not
  `SurfaceMesh` by default.
- `SHREC16` loads OBJ files; test split has no category metadata.
- Wrapper `get_cache_key(index)` returns the model name, useful for cache keys.
- `CachedDataset` requires dictionary outputs and may cache selected keys to
  disk as `.pt` files; it does not make remote dataset downloads safe or cheap.
