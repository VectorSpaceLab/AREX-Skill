# Troubleshooting

Use this guide to diagnose geometry and I/O failures before routing to other
sub-skills. For expected shapes and signatures, see
[API reference](api-reference.md); for dispatch rules, see
[data formats](data-formats.md).

## Fast triage checklist

1. Run the safe helper without importing Kaolin:

   ```bash
   python scripts/mesh_io_probe.py --help
   ```

2. Check installed imports and optional USD availability:

   ```bash
   python scripts/mesh_io_probe.py --check-imports --json
   ```

3. If a file fails to load, probe the exact file and mode:

   ```bash
   python scripts/mesh_io_probe.py --kind mesh ./asset.obj --triangulate --json
   python scripts/mesh_io_probe.py --kind gaussian ./scene.ply --json
   python scripts/mesh_io_probe.py --kind usd-paths ./stage.usdc --json
   ```

4. Record the exception class/message, file suffix, chosen importer, optional
   dependencies, and tensor shapes before changing code.

## Import and environment failures

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError` while importing `kaolin` | Missing package dependency in the Python environment. Some source-style installs import utility dependencies transitively. | Install the missing dependency or switch to a complete Kaolin runtime. `mesh_io_probe.py --help` should still work because it delays Kaolin imports. |
| `kaolin.io.usd` is missing or warns that USD is not installed | `pxr` / `usd-core` is not installed. | Treat USD as optional-gated. Use OBJ/GLTF/PLY paths when possible, or install a compatible USD package before USD import/export. |
| `ImportError: Cannot use usd import features, usd-core is not installed` | Generic mesh/Gaussian selector reached a USD path without `pxr`. | Re-run with `--kind usd-paths` after installing USD, or choose a non-USD format. |
| `from kaolin.rep import GaussianSplatModel` fails in a wheel | Source/wheel re-export drift. | Check package version and try the documented module path for the installed build. Do not assume the data workflow is impossible until module availability is confirmed. |
| CUDA/nvdiffrast/Warp/Jupyter/browser errors | The requested task is outside pure geometry/IO. | Route rendering to `rendering-cameras-lighting`, physics to `physics-simulation`, UI to `visualization-workflows`, and tensor kernels/conversions to `ops-metrics-conversions`. |

## `SurfaceMesh` constructor and batching errors

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: Illegal inputs passed to SurfaceMesh constructor` | Tensor shapes do not match inferred batching. | Print `SurfaceMesh.attribute_info_string(mesh.batching)` if construction succeeded, or compare against the shape table in [API reference](api-reference.md). |
| A LIST batch fails strict checks | LIST batching requires each tensor attribute to be a list with one tensor per mesh, except `transform`, which is a tensor `(4,4)` or `(B,4,4)`. | Convert every per-mesh attribute to aligned lists; keep transforms as a broadcast or batched tensor. |
| A FIXED batch fails | Only `faces` is fixed topology; most other tensor attributes need a batch dimension. | Use `vertices: (B,V,3)`, `faces: (F,FSz)`, and `material_assignments: (B,F)`. If topology varies, use LIST batching. |
| `mesh.to_batched()` or `set_batching(FIXED)` fails from LIST | LIST meshes have incompatible topology or shape. | Use `SurfaceMesh.cat(meshes, fixed_topology=False)` for LIST batching or homogenize first. |
| `get_attribute(attr)` returns `None` but direct access computes a value | `get_attribute` never auto-computes; `__getattr__` and `get_or_compute_attribute` can. | Use `has_attribute`, then `get_or_compute_attribute(attr, should_cache=...)` when derived values are acceptable. |
| Auto-computed values unexpectedly are not cached | An upstream tensor has `requires_grad=True`. | Force caching with `should_cache=True` only when it is safe for the optimization graph. |
| Downstream API needs indexed normals/UVs but mesh has `face_normals` or `face_uvs` | USD/flattened mesh can store face-varying values without indexed pools. | Use `mesh.ensure_indexed_attribute("normals")` or `mesh.ensure_indexed_attribute("uvs")`; route lower-level tensor manipulation to ops if needed. |

## Heterogeneous and non-triangular meshes

| Symptom | Cause | Fix |
|---|---|---|
| `NonHomogeneousMeshError` from OBJ/USD import | Faces have varying vertex counts and no handler was supplied. | Pass `triangulate=True` or `heterogeneous_mesh_handler=kaolin.io.utils.mesh_handler_naive_triangulate`. |
| Import returns `None` or omits a USD mesh | Handler intentionally skipped a heterogeneous mesh. | Decide whether skip is acceptable; otherwise use triangulation or a custom handler. |
| Face count/material assignments changed after import | Triangulation split faces and remapped assignments. | Validate `faces.shape[0]`, `material_assignments.shape`, and material counts after import. |
| `face_normals` cannot be auto-computed | Mesh is not triangular and lacks indexed normals/vertex normals. | Load normals from the file (`with_normals=True`), triangulate, or compute normals in an ops workflow. |

## OBJ and material failures

| Symptom | Cause | Fix |
|---|---|---|
| `MaterialFileError` | Referenced `.mtl` file cannot be opened. | Use `obj.skip_error_handler` to warn/continue, or fix the material path. |
| `MaterialLoadError` | Texture map or MTL field failed to load. | Use `skip_error_handler` for permissive imports; inspect texture paths and image dependencies. |
| `MaterialNotFoundError` | A `usemtl` reference has no loaded material definition. | Use `obj.create_missing_materials_error_handler` to insert dummy materials, or correct the MTL. |
| Raw material dicts do not match glTF/USD `PBRMaterial` | OBJ direct import defaults to `raw_materials=True`. | Pass `raw_materials=False` when you need a common PBR material object, or preserve raw dicts intentionally. |
| Material assignment values are out of range | `materials` list and `material_assignments` were modified independently. | Ensure `material_assignments` is length `F` and every nonnegative value is `< len(materials)`. |
| Device conversion leaves custom materials unchanged | Only `PBRMaterial` tensors are converted by `SurfaceMesh.to/cuda/cpu`; arbitrary custom material classes are preserved. | Convert custom material tensors manually or keep materials on CPU. |

## GLTF / GLB import warnings

| Symptom | Cause | Action |
|---|---|---|
| Warning about unsupported primitive `mode` | The loader only supports triangle primitives (`mode == 4`) for full mesh data. | Expect skipped/empty primitives; use a GLTF preprocessing tool if needed. |
| Warning about vertex colors | Current importer does not load vertex colors. | Preserve color data externally or use another format/workflow if vertex colors are required. |
| Warning about vertex skinning | Current importer does not apply skinning; mesh may load in canonical pose. | Use an asset pre-exported/baked into geometry, or route animation/skinning requirements outside this sub-skill. |
| Warning about sampler wrapping | Certain texture wrapping modes are unsupported. | Imported texture tensors may still load, but rendering behavior can differ; route render semantics to rendering sub-skill. |
| Material fields do not match another format exactly | glTF PBR workflows and USD Preview Surface/OBJ MTL have different conventions. | Compare supported `PBRMaterial` fields and tolerate minor numeric/image differences after format conversion. |

## PLY Gaussian failures

| Symptom | Cause | Fix |
|---|---|---|
| Key error or parser failure for `x`, `y`, `z`, `opacity`, `f_dc_*`, `scale_*`, or `rot_*` | File is not a 3DGS Gaussian PLY or required fields are absent. | Inspect PLY property names; use the correct reader for generic mesh PLY, or add required Gaussian fields. |
| `sh_degree` or `sh_coeff` error | Number of SH coefficients is not a perfect square after DC and rest coefficients are assembled. | Ensure `sh_coeff.shape[1] == (degree+1)^2`. Standard degree 0 uses `1`; degree 3 uses `16`. |
| `features` export raises `ValueError` | Feature value is not a dict of `(N,K)` tensors, a key is non-string/reserved, rank is wrong, or point count differs. | Use `features={"name": tensor}` with each tensor shape `(N,K)` and avoid reserved prefixes. |
| Extra PLY field is ignored | Extra field lacks a `_<integer>` suffix. | Name grouped feature columns as `feature_0`, `feature_1`, ...; names may contain underscores before the last suffix. |
| Imported scales/opacities/rotations look transformed from raw file values | `apply_activations=True` applies sigmoid/exp/normalize by default. | Pass `apply_activations=False` to inspect raw PLY values, then activate deliberately. |
| Destination exists on export | `overwrite=False` is the default. | Pass `overwrite=True` only when replacing the file is intended. |

## USD Gaussian failures

| Symptom | Cause | Fix |
|---|---|---|
| No Gaussian paths found | Stage contains no `ParticleField3DGaussianSplat` prims under the selected prefix. | Run `mesh_io_probe.py --kind usd-paths stage.usdc` and adjust `scene_path`. |
| Assertion that prim is not `ParticleField3DGaussianSplat` | Wrong scene path or unsupported USD representation. | Use `get_gaussiancloud_scene_paths` and pass one of those paths. |
| `positions must be provided`, `orientations must be provided`, etc. | Export called without required standard tensor. | Supply all five tensors: positions, orientations, scales, opacities, and `sh_coeff`. |
| Shape assertion for positions/orientations/scales/opacities | Tensor ranks or lengths do not match `N`. | Use `(N,3)`, `(N,4)`, `(N,3)`, `(N,)` or squeeze `(N,1)` opacities. |
| `sh_coeff.shape[1] must be a perfect square` | SH coefficient count is invalid. | Build coefficient tensor with second dimension `(degree+1)^2`. |
| Existing prim error in `add_gaussiancloud` | A prim exists at the scene path and `overwrite=False`. | Use a new absolute scene path or pass `overwrite=True` after confirming replacement. |
| Merged clouds lose higher SH bands or fail to concatenate | Clouds have mismatched SH coefficient counts. | Normalize SH degree before export/import, or intentionally call `GaussianSplatModel.cat(..., skip_errors=True)` after separate imports. |
| Half-precision tensors surprise downstream code | Compressed USD may import half tensors. | Cast with `.to(dtype=torch.float32)` before handing to code that assumes float32. |

## USD mesh and point-cloud failures

| Symptom | Cause | Fix |
|---|---|---|
| `File does not exist` | Path is wrong or exporter was called without existing output directory. | Ensure directories exist before `create_stage`/export and paths are correct. |
| Invalid `scene_path` or no prim found | Scene path is not absolute or does not match the stage. | Use `get_mesh_scene_paths`, `get_pointcloud_scene_paths`, or `get_scene_paths` to discover valid paths. |
| UV interpolation not supported | USD UV primvar uses interpolation other than `vertex`, `varying`, or `faceVarying`. | Preprocess USD to supported interpolation or handle UVs outside Kaolin import. |
| `face_uvs_idx` warning on export | `face_uvs_idx` supplied without `uvs`. | Supply both `uvs` and `face_uvs_idx`, or omit both. |
| Point-cloud colors missing after import | Colors are only written/read for `points_type='usd_geom_points'`; point instancers do not preserve colors. | Export with `points_type='usd_geom_points'` when colors matter. |
| Point-cloud normals are `None` | Normals are not implemented by the point-cloud importer. | Preserve normals in a separate feature tensor or route a custom USD path. |
| Transform appears transposed | Confusion between USD matrix convention and Kaolin tensor convention. | Use `get_local_to_world_transform` and `set_local_to_world_transform`; Kaolin tensors use translation in the last column. |

## Dataset and cache failures

| Symptom | Cause | Fix |
|---|---|---|
| `CachedDataset` says item must output a dictionary | Dataset wrapper was built with deprecated `output_dict=False`. | Recreate dataset with `output_dict=True` or wrap namedtuple output into a dict. |
| Cache directory count mismatch | Existing cache has a different number of item directories than the dataset length. | Use a new cache directory or pass `force_overwrite=True` after confirming it is safe. |
| Cached value differs from fresh value | Dataset/preprocessing changed, or cache is stale. | Use `force_overwrite=True`; use `ignore_diff_error=True` only when stale/different cache is intentionally accepted. |
| Multiprocessing cache fails with CUDA tensors | CUDA preprocessing in worker processes is unsafe for this wrapper. | Set `num_workers=0` when preprocessing touches CUDA. |
| Dataset category assertion fails | Category name/synset is unsupported or not present under root. | Verify category spelling and dataset root layout; ShapeNet accepts synset IDs or known labels. |
| ModelNet output is not a `SurfaceMesh` | ModelNet uses OFF importer and returns an OFF namedtuple. | Convert to `SurfaceMesh` manually if needed. |

## When to stop and route

Stop using this sub-skill and hand off when the next step is:

- Sampling, voxel/SPC conversion, metrics, losses, or tensor kernels.
- Rendering, camera projection, lighting, or shader behavior.
- Browser/Jupyter/Dash3D/Timelapse UI behavior.
- Simplicits/Newton/physics simulation.

Always include the normalized container contract, file format, import flags,
material policy, device/dtype, and unresolved optional dependencies in the
handoff.
