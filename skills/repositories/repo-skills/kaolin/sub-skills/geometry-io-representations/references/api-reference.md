# API reference

This is the self-contained API map for Kaolin geometry containers and data I/O.
Use [data formats](data-formats.md) for dispatch rules and
[troubleshooting](troubleshooting.md) for failure diagnosis.

## Import stance

Prefer public installed-package APIs. A normal workflow starts with one of:

```python
import kaolin as kal
from kaolin.rep import SurfaceMesh, Spc, PointSamples, GaussianSplatModel
from kaolin.io import obj, off, gltf, ply, usd
```

If a wheel is older than the source evidence used to build this skill, a new
Gaussian class or helper may not be re-exported at the top level. Treat that as
source/wheel drift: verify the package version and module path before changing
the workflow.

## Representation containers

### `kaolin.rep.SurfaceMesh`

Constructor signature:

```python
SurfaceMesh(
    vertices, faces,
    normals=None, uvs=None, face_uvs_idx=None, face_normals_idx=None,
    material_assignments=None, materials=None,
    vertex_normals=None, vertex_tangents=None, vertex_colors=None,
    vertex_features=None, face_normals=None, face_uvs=None,
    face_vertices=None, face_tangents=None, face_colors=None,
    face_features=None, transform=None,
    strict_checks=True, unset_attributes_return_none=True,
    allow_auto_compute=True,
)
```

`SurfaceMesh` stores PyTorch tensors and optional material objects. The batching
strategy is inferred at construction time.

| Batching | When inferred | Core shapes | Material shape | Transform shape |
|---|---|---|---|---|
| `SurfaceMesh.Batching.NONE` | Single mesh tensors | `vertices: (V,3)`, `faces: (F,FSz)` | list of materials | `(4,4)` |
| `SurfaceMesh.Batching.FIXED` | `vertices` is `(B,V,3)` and `faces` is fixed topology | per-mesh tensors are `(B,...)`; `faces` remains `(F,FSz)` | list of lists | `(4,4)` broadcast or `(B,4,4)` |
| `SurfaceMesh.Batching.LIST` | `vertices` or `faces` is a list, or `faces` is 3D | lists of per-mesh tensors, e.g. `[V_i,3]` and `[F_i,FSz_i]` | list of lists | `(4,4)` broadcast or `(B,4,4)` |

Common tensor attributes:

| Attribute | `NONE` shape | Meaning |
|---|---:|---|
| `vertices` | `(V,3)` float | XYZ vertex positions. |
| `faces` | `(F,FSz)` int/long | Indices into `vertices`; `FSz=3` for triangle meshes, but homogeneous quads/polygons are allowed when all faces have the same size. |
| `normals` | `(VN,3)` float | Indexed normal pool. |
| `face_normals_idx` | `(F,FSz)` int/long | Indices into `normals`. |
| `face_normals` | `(F,FSz,3)` float | Per-face-per-vertex normals; auto-computable from indexed normals, vertex normals, or triangular geometry. |
| `uvs` | `(U,2)` float | UV pool. |
| `face_uvs_idx` | `(F,FSz)` int/long | Indices into `uvs`. |
| `face_uvs` | `(F,FSz,2)` float | Per-face-per-vertex UVs; auto-computable from `uvs` and `face_uvs_idx`. |
| `face_vertices` | `(F,FSz,3)` float | Vertex positions indexed by face; auto-computable from `faces` and `vertices`. |
| `vertex_normals`, `vertex_tangents`, `vertex_colors`, `vertex_features` | `(V,C)` style | Per-vertex values; some are auto-computable from face values. |
| `face_tangents`, `face_colors`, `face_features` | `(F,FSz,C)` style | Per-face-per-vertex values. |
| `material_assignments` | `(F,)` int/short | Index into `materials` for each face, or `-1` for no material. |
| `transform` | `(4,4)` | Stored local-to-world transform; not applied until `as_transformed()` or `flatten()`. |

Useful methods:

| Method | Use |
|---|---|
| `check_sanity()` | Validate tensor shapes for the inferred batching strategy. |
| `to_string(print_stats=False, detailed=False)` / `describe_attribute(attr)` | Print shape, dtype, device, and optional stats. |
| `get_attributes(only_tensors=False)` / `has_attribute(attr)` | Inspect which attributes are set without triggering auto-compute. |
| `get_attribute(attr)` | Return only explicitly set attributes; honors `unset_attributes_return_none`. |
| `get_or_compute_attribute(attr, should_cache=None)` | Compute supported derived attributes, optionally forcing or preventing cache. |
| `ensure_indexed_attribute("normals"|"uvs")` | Convert `face_normals`/`face_uvs` into indexed pools when a downstream API requires indexed values. |
| `set_batching(batching, skip_errors=False)` / `to_batched()` / `getattr_batched(attr, batching)` | Convert between `NONE`, `FIXED`, and `LIST`; fails when the target batching is not representable. |
| `SurfaceMesh.cat(meshes, fixed_topology=True, skip_errors=False)` | Batch meshes while preserving transforms; `fixed_topology=False` creates `LIST` batching. |
| `SurfaceMesh.flatten(meshes, skip_errors=False, group_materials_by_name=False)` | Apply stored transforms, concatenate indexed attributes correctly, and return one world-space `NONE` mesh. |
| `cuda()`, `cpu()`, `to(device)`, `float_tensors_to(dtype)`, `detach()` | Shallow-copy tensor/device helpers; can target selected attributes. |
| `as_transformed()` | Return a new mesh with stored transform applied to vertices and direction attributes; transform is cleared. |

Auto-computable attributes include `face_vertices`, `face_normals`,
`vertex_normals`, `face_uvs`, `vertex_tangents`, `face_tangents`,
`vertex_colors`, `face_colors`, `vertex_features`, and `face_features`. Auto
caching is disabled when upstream tensors require gradients unless explicitly
forced.

### `kaolin.rep.Spc`

Constructor signature:

```python
Spc(octrees, lengths, max_level=None, pyramids=None,
    exsum=None, point_hierarchies=None, features=None)
```

SPC is only represented here as a container. Kernel operations, conversions,
queries, convolution, and metrics belong to `ops-metrics-conversions`.

| Field | Expected contract |
|---|---|
| `octrees` | 1D `torch.uint8` tensor; each byte encodes 8 child-cell occupancy bits. |
| `lengths` | 1D `torch.int` tensor with one length per packed SPC in the batch. |
| `max_level` | `int` or `None`; computed lazily by `scan_octrees` when needed. |
| `pyramids` | `torch.int`, shape `(batch_size, 2, max_level + 2)`, CPU tensor. |
| `exsum` | 1D `torch.int`, same device as `octrees`; legacy layouts may be normalized with a warning. |
| `point_hierarchies` | `torch.short`, shape `(num_nodes, 3)`, same device as `octrees`. |
| `features` | Optional tensor, same device as `octrees`; one feature per highest-resolution point. |

Convenience constructors and accessors:

- `Spc.make_dense(level, device="cuda")` creates a dense fully occupied SPC using ops.
- `Spc.from_features(feature_grids, masks=None)` converts feature grids via ops.
- `Spc.from_list(octrees_list)` packs a list of 1D byte octrees.
- `spc.max_level`, `spc.pyramids`, `spc.exsum`, and `spc.point_hierarchies` are lazy.
- `spc.to(device)`, `spc.cuda()`, and `spc.cpu()` move `octrees` and derived same-device tensors; `lengths` stays as batching metadata.
- `spc.to_dict(keys=None)`, `spc.batch_size`, and `spc.num_points(lod)` support inspection.

### `kaolin.rep.TensorContainerBase`

Abstract base for tensor-rich containers. Subclasses define:

- `class_tensor_attributes()` for tensor or dict-of-tensors attributes.
- `class_other_attributes()` for non-tensor attributes.
- `check_tensor_attribute(attr, log_error=False)` and optionally
  `check_other_attribute(attr, log_error=False)`.

Provided utilities: `to`, `cuda`, `cpu`, `detach`, `get_attributes`, `as_dict`,
`describe_attribute`, `check_sanity`, `to_string`, `__repr__`, and `__str__`.
Dict-valued tensor attributes are moved/described key-by-key.

### `kaolin.rep.PointSamples`

Constructor signature:

```python
PointSamples(positions, features=None, transform=None, strict_checks=True)
```

| Attribute | Shape/type | Notes |
|---|---|---|
| `positions` | `(N,3)` tensor | Required XYZ point positions. |
| `features` | `None`, tensor `(N, ...)`, or dict of tensors `(N, ...)` | Optional per-point channels; every value must have first dimension `N`. |
| `transform` | `None`, `(4,4)`, `(1,4,4)`, or `(N,4,4)` tensor | Stored affine transform; `as_transformed()` applies it to positions. |

Point-level utilities inherited or implemented by `PointSamples`: `cat`,
masking via `obj[mask]`, assignment via `obj[mask] = other`, `as_transformed`,
`len(obj)`, `as_dict`, device/dtype conversion, and shape validation.

### `kaolin.rep.GaussianSplatModel`

Constructor signature:

```python
GaussianSplatModel(
    positions, orientations, scales, opacities, sh_coeff,
    features=None, transform=None, sh_degree=None, strict_checks=True,
)
```

All Gaussian attributes are stored in post-activation/final range.

| Attribute | Shape/type | Notes |
|---|---|---|
| `positions` | `(N,3)` float tensor | Splat centers. |
| `orientations` | `(N,4)` float tensor | Unit quaternions in `(w,x,y,z)` convention; normalized by the constructor. |
| `scales` | `(N,3)` float tensor | Per-axis scale, post activation. |
| `opacities` | `(N,)` float tensor | Per-splat opacity, post activation. |
| `sh_coeff` | `(N,S,3)` float tensor | Spherical harmonics coefficients; `S=(sh_degree+1)^2`. |
| `features` | optional tensor/dict with first dim `N` | Extra per-Gaussian channels. |
| `transform` | `None`, `(4,4)`, `(1,4,4)`, or `(N,4,4)` | Stored transform; `as_transformed()` applies it. |
| `sh_degree` | `int` | Inferred from `sh_coeff.shape[1]` if omitted. |

Class helpers:

- `GaussianSplatModel.compute_sh_degree(num_sh_coeff)` requires a perfect square.
- `GaussianSplatModel.compute_num_sh_coeff(sh_degree)` returns `(sh_degree+1)^2`.
- `GaussianSplatModel.cat(models, skip_errors=False)` concatenates point-level
  attributes. If SH coefficient counts differ, it raises by default; with
  `skip_errors=True` it caps `sh_coeff` to the smallest count.
- `as_transformed(additional_transform=None)` applies stored and/or additional
  affine transforms to positions, orientations, scales, and SH coefficients.
  It is robust for rotation, translation, and isotropic scale; shear or
  anisotropic scaling can be surprising.

## Mesh and Gaussian I/O functions

### Generic selectors

| API | Signature | Dispatch | Return |
|---|---|---|---|
| `kaolin.io.import_mesh` / `kaolin.io.mesh.import_mesh` | `import_mesh(filename, triangulate=False)` | `.obj`, `.usd/.usda/.usdc/.usdz`, `.gltf/.glb` | `SurfaceMesh` or `None` for no USD meshes |
| `kaolin.io.import_gaussiancloud` / `kaolin.io.gaussians.import_gaussiancloud` | `import_gaussiancloud(filename)` | `.ply`, `.usd/.usda/.usdc/.usdz` | `GaussianSplatModel` or `None` for empty USD |

The generic mesh selector does not support OFF and does not expose USD
`scene_path`/`time`; use format-specific APIs for those.

### OBJ/OFF/GLTF/PLY

| API | Signature | Important behavior |
|---|---|---|
| `kaolin.io.obj.import_mesh` | `import_mesh(path, with_materials=False, with_normals=False, error_handler=None, heterogeneous_mesh_handler=None, triangulate=False, raw_materials=True)` | Returns CPU `SurfaceMesh`; OBJ indices become zero-based; `triangulate=True` uses naive triangulation; `raw_materials=False` converts supported MTL fields to `PBRMaterial`. |
| `kaolin.io.obj.load_mtl` | `load_mtl(mtl_path, error_handler)` | Parses MTL `Kd`, `Ka`, `Ks`, texture maps, bump/disp/opacity/roughness/metallic-like maps into raw tensors. |
| `kaolin.io.off.import_mesh` | `import_mesh(path, with_face_colors=False)` | Returns namedtuple `vertices`, `faces`, `face_colors`; not a `SurfaceMesh`. |
| `kaolin.io.gltf.import_mesh` | `import_mesh(path, scene=None)` | Loads default or selected glTF scene, applies node transforms, flattens scene meshes, and returns `SurfaceMesh`. |
| `kaolin.io.gltf.import_meshes` | `import_meshes(path)` | Returns uncomposed mesh list with local material assignments. |
| `kaolin.io.ply.import_gaussiancloud` | `import_gaussiancloud(filename, apply_activations=True, scale_activation=torch.exp, rotation_activation=torch.nn.functional.normalize, density_activation=torch.sigmoid)` | Reads 3D Gaussian Splat PLY into `GaussianSplatModel`; standard fields are activated by default. |
| `kaolin.io.ply.export_gaussiancloud` | `export_gaussiancloud(file_path, positions, orientations, scales, opacities, sh_coeff, features=None, sh_degree=None, overwrite=False)` | Writes standard 3DGS PLY fields and optional extra feature groups; raises if destination exists and `overwrite=False`. |

### USD mesh, point cloud, Gaussian, material, and stage helpers

USD APIs require `pxr`/`usd-core` to be importable.

| API | Signature | Return/behavior |
|---|---|---|
| `kaolin.io.usd.get_mesh_scene_paths` | `get_mesh_scene_paths(file_path_or_stage, scene_path=None)` | List mesh prim paths, optionally under a prefix. |
| `kaolin.io.usd.import_mesh` | `import_mesh(file_path_or_stage, scene_path=None, with_materials=False, with_normals=False, heterogeneous_mesh_handler=None, time=None, triangulate=False)` | Imports all matching mesh prims, applies transforms, and returns one world-space `SurfaceMesh` or `None`. |
| `kaolin.io.usd.import_meshes` | `import_meshes(file_path_or_stage, scene_paths=None, with_materials=False, with_normals=False, heterogeneous_mesh_handler=None, times=None, triangulate=False, return_list=True)` | Imports one mesh per path; list by default, dict when `return_list=False`. |
| `kaolin.io.usd.add_mesh` | `add_mesh(stage, scene_path, vertices=None, faces=None, uvs=None, face_uvs_idx=None, face_normals=None, material_assignments=None, materials=None, local_to_world=None, time=None, overwrite_textures=False)` | Mutates an open stage; does not save the stage. |
| `kaolin.io.usd.export_mesh` | `export_mesh(file_path, scene_path='/World/Meshes/mesh_0', vertices=None, faces=None, uvs=None, face_uvs_idx=None, face_normals=None, material_assignments=None, materials=None, local_to_world=None, up_axis='Y', time=None, overwrite_textures=False, overwrite=False)` | Creates/saves a stage with one mesh; overwrite is explicit. |
| `kaolin.io.usd.export_meshes` | `export_meshes(file_path, scene_paths=None, vertices=None, faces=None, uvs=None, face_uvs_idx=None, face_normals=None, material_assignments=None, materials=None, local_to_world=None, up_axis='Y', times=None, overwrite_textures=False, overwrite=False)` | Writes lists of mesh tensors; list-valued inputs must have equal length. |
| `kaolin.io.usd.get_pointcloud_scene_paths` | `get_pointcloud_scene_paths(file_path_or_stage, scene_path=None)` | Lists `Points` and `PointInstancer` paths. |
| `kaolin.io.usd.import_pointcloud` | `import_pointcloud(file_path_or_stage, scene_path=None, time=None)` | Merges point clouds into world-space namedtuple `(points, colors, normals, transform)`; transform is `None` after merge. |
| `kaolin.io.usd.import_pointclouds` | `import_pointclouds(file_path_or_stage, scene_paths=None, times=None, return_list=True)` | Returns local-space pointcloud namedtuples with optional `transform`. |
| `kaolin.io.usd.export_pointcloud` | `export_pointcloud(file_path, scene_path='/World/PointClouds/pointcloud_0', points=None, colors=None, local_to_world=None, up_axis='Y', time=None, points_type='point_instancer', overwrite=False, pointcloud=None, color=None)` | Writes one point cloud as `PointInstancer` or `UsdGeomPoints`; old aliases warn. |
| `kaolin.io.usd.export_pointclouds` | `export_pointclouds(file_path, scene_paths=None, points=None, colors=None, local_to_world=None, up_axis='Y', times=None, points_type='point_instancer', overwrite=False, pointclouds=None)` | Writes a point-cloud list; `local_to_world` may be `(4,4)` or `(N,4,4)`. |
| `kaolin.io.usd.get_gaussiancloud_scene_paths` | `get_gaussiancloud_scene_paths(file_path_or_stage, scene_path=None)` | Lists `ParticleField3DGaussianSplat` paths. |
| `kaolin.io.usd.import_gaussianclouds` | `import_gaussianclouds(file_path_or_stage, scene_paths=None, times=None, return_list=True)` | Returns local-space `GaussianSplatModel` list/dict with optional `transform`. |
| `kaolin.io.usd.import_gaussiancloud` | `import_gaussiancloud(file_path_or_stage, scene_path=None, time=None)` | Imports matching Gaussian prims, applies transforms, concatenates, and returns one world-space `GaussianSplatModel` or `None`. |
| `kaolin.io.usd.add_gaussiancloud` | `add_gaussiancloud(stage, scene_path, positions, orientations, scales, opacities, sh_coeff, local_to_world=None, time=None, overwrite=False)` | Mutates an open stage with one `ParticleField3DGaussianSplat`; shape checks are strict. |
| `kaolin.io.usd.export_gaussiancloud` | `export_gaussiancloud(file_path, scene_path='/World/Gaussians/gaussian_0', positions=None, orientations=None, scales=None, opacities=None, sh_coeff=None, local_to_world=None, up_axis='Y', time=None, overwrite=False)` | Creates/saves one Gaussian prim; all standard Gaussian tensors are required. |
| `kaolin.io.usd.import_material` | `import_material(file_path_or_stage, scene_path, texture_path=None, time=None)` | Reads registered shader material, usually `UsdPreviewSurface`, into `PBRMaterial` or raw parameters. |
| `kaolin.io.usd.export_material` | `export_material(pbr_material, file_path_or_stage, scene_path=None, texture_path=None, bound_prims=None, texture_file_prefix=None, shader_name=None, time=None, overwrite_textures=False)` | Writes material and textures to USD; unsupported inputs warn or fail by field. |
| `kaolin.io.usd.create_stage` | `create_stage(file_path, up_axis='Y')` | Creates a new stage, defines `/World`, sets default prim and up axis. |
| `kaolin.io.usd.get_scene_paths` | `get_scene_paths(file_path_or_stage, scene_path_regex=None, prim_types=None, conditional=lambda x: True)` | General USD path enumeration. |
| `kaolin.io.usd.get_authored_time_samples` | `get_authored_time_samples(file_path_or_stage)` | Sorted list of all authored USD time samples. |
| `kaolin.io.usd.get_local_to_world_transform` / `set_local_to_world_transform` | `(file_path_or_stage, prim_or_path, time=None)` / `(file_path_or_stage, prim_or_path, local_to_world, time=None)` | Uses Kaolin tensor convention `(4,4)` with translation in the last column; identity reads as `None`. |

## Materials

`kaolin.render.materials.PBRMaterial` is the common material object used by USD,
glTF, and optional OBJ conversion. Supported value fields include diffuse,
roughness, metallic, clearcoat, opacity, opacity threshold, IOR, specular,
displacement, and transmittance. Supported texture fields include diffuse,
roughness, metallic, clearcoat, opacity, IOR, specular, normals, displacement,
and transmittance textures. Color-space fields are strings such as `auto`,
`raw`, or `sRGB` depending on the texture channel.

Key operational points:

- OBJ direct import returns raw MTL dicts by default. Pass `raw_materials=False`
  to convert supported fields to `PBRMaterial`.
- glTF import returns `PBRMaterial` instances and composes scene transforms.
- USD material export targets `UsdPreviewSurface` by default and writes textures
  next to the stage unless `texture_path` is specified.
- `material_assignments` must align with face count and index the `materials`
  list. `-1` means no material.
- `SurfaceMesh.flatten(..., group_materials_by_name=True)` can deduplicate
  same-named materials and remap assignments.

## Dataset wrappers and caching

| API | Signature | Item output |
|---|---|---|
| `kaolin.io.shapenet.ShapeNetV1` | `ShapeNetV1(root, categories=None, train=True, split=.7, with_materials=True, transform=None, output_dict=False)` | ShapeNet OBJ `SurfaceMesh` plus `name`, `path`, `synset`, `labels`. |
| `kaolin.io.shapenet.ShapeNetV2` | `ShapeNetV2(root, categories=None, train=True, split=.7, with_materials=True, transform=None, output_dict=False)` | ShapeNet V2 normalized OBJ `SurfaceMesh` plus metadata. |
| `kaolin.io.modelnet.ModelNet` | `ModelNet(root, categories=None, split='train', transform=None, output_dict=False)` | OFF namedtuple `mesh` plus `name`, `path`, `label`. |
| `kaolin.io.shrec.SHREC16` | `SHREC16(root, categories=None, split='train', transform=None, output_dict=False)` | OBJ `SurfaceMesh` plus `name`, `path`, `synset`, `labels`; test split has no category metadata. |
| `kaolin.io.dataset.CachedDataset` | `CachedDataset(dataset, cache_dir=None, save_on_disk=False, num_workers=0, force_overwrite=False, cache_at_runtime=False, progress_message=None, ignore_diff_error=False, transform=None)` | Caches dictionary outputs in RAM and/or `.pt` files. |

Prefer `output_dict=True` for dataset wrappers when composing with
`CachedDataset`. The legacy `output_dict=False` path returns a deprecated
`KaolinDatasetItem` namedtuple and is not suitable for the current cache wrapper,
which requires dataset items to be dictionaries.
