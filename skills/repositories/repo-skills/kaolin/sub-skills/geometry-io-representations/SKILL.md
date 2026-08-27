---
name: geometry-io-representations
description: "Operate Kaolin geometry containers and data I/O for SurfaceMesh,
  SPC, point samples, Gaussian splats, mesh formats, USD assets, materials, and
  dataset wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# geometry-io-representations

Use this sub-skill when a Kaolin task is about **representing, loading,
saving, validating, or diagnosing 3D data containers and file formats**. It is
an operating router for geometry/IO context; do not reopen the source repository
or notebooks at runtime.

## Read first

- [API reference](references/api-reference.md) for representation constructors,
  tensor shape/device contracts, dataset wrappers, and public I/O signatures.
- [Data formats](references/data-formats.md) for OBJ/OFF/GLTF/PLY/USD dispatch,
  materials, Gaussian/point-cloud schemas, and USD path/time conventions.
- [Workflows](references/workflows.md) for common mesh, Gaussian, point-sample,
  USD, and cached-dataset plans.
- [Troubleshooting](references/troubleshooting.md) for import failures,
  heterogeneous meshes, material issues, Gaussian schema problems, USD/`pxr`,
  and cache pitfalls.
- [Safe I/O probe](scripts/mesh_io_probe.py) for non-mutating importer checks;
  `--help` works without importing Kaolin.

## Use when

- A task mentions `SurfaceMesh`, `Spc`, `TensorContainerBase`, `PointSamples`,
  `GaussianSplatModel`, mesh/point/Gaussian container construction, batching,
  `transform`, material assignments, or attribute inspection.
- A task asks to import or export OBJ/OFF/GLTF/GLB/PLY/USD/USDA/USDC/USDZ data,
  choose `kaolin.io.import_mesh`, use format-specific importers/exporters, or
  diagnose mesh/Gaussian file schema problems.
- A user needs USD stage/scene-path/time handling, point-cloud or Gaussian USD
  read/write, local-to-world transform handling, or `pxr` availability guidance.
- A task involves ShapeNet, ModelNet, SHREC, `CachedDataset`, dataset cache keys,
  cache-on-disk/RAM behavior, or dataset wrapper output shape.
- A mesh workflow needs material/UV/normal preservation, heterogeneous face-size
  handling, or safe triangulation/skipping decisions.

## Route elsewhere

- Low-level tensor conversions, sampling, packed/padded utilities, mesh/point/
  voxel/SPC operations, metrics, losses, quaternion math, SPC kernels, or
  Gaussian tensor ops beyond container/I/O: route to `ops-metrics-conversions`.
- Cameras, lighting, differentiable rendering, rasterization, DIB-R,
  nvdiffrast, or PBR image generation: route to `rendering-cameras-lighting`.
- Timelapse logs, notebook widgets, Dash3D/web visualizers, GLTF UI display, or
  browser/Jupyter troubleshooting: route to `visualization-workflows`.
- Simplicits, Newton, collision/material simulation, training/baking, or
  physics-scene stepping: route to `physics-simulation`.

## Operating rules

1. **Normalize the representation first.** Decide whether the user has a
   `SurfaceMesh`, an SPC container, generic point samples, a Gaussian splat
   cloud, a USD point cloud namedtuple, an OFF namedtuple, or a dataset item.
2. **Choose importers deliberately.** `kaolin.io.import_mesh` is the generic
   mesh selector for OBJ/USD/GLTF/GLB; OFF and Gaussian PLY need format-specific
   or Gaussian selectors. Use format-specific USD/OBJ calls when scene paths,
   material flags, normals, times, or heterogeneous handlers matter.
3. **State tensor contracts.** Keep shapes, dtype, device, batching strategy,
   and optional `transform` behavior explicit before handing tensors to ops,
   rendering, or physics sub-skills.
4. **Treat materials and heterogeneity as first-class.** Confirm whether
   materials are raw OBJ dicts or `PBRMaterial`, whether `material_assignments`
   length matches faces, and whether non-triangular/heterogeneous faces should
   be triangulated, skipped, or rejected.
5. **Gate optional dependencies.** USD requires `pxr`/`usd-core`; rendering,
   physics, browser, Jupyter, Warp, CUDA, and nvdiffrast are not required for
   this sub-skill's default probes. Record missing optional dependencies instead
   of running expensive defaults.
6. **Account for source/wheel drift.** Some installed wheels can lag newer
   Gaussian container or I/O re-exports. If a top-level import is missing,
   verify the module path documented here and treat the mismatch as an
   environment/version warning, not as proof the workflow is impossible.
7. **Do not depend on checkout paths.** Use only installed Kaolin APIs and these
   bundled references/scripts at runtime.

## Minimal decision flow

1. Identify the artifact type and desired output container (`SurfaceMesh`,
   `GaussianSplatModel`, point cloud namedtuple, OFF tuple, dataset item, or
   raw tensor plan).
2. Select the importer/exporter family from [Data formats](references/data-formats.md).
3. Validate shapes/devices with [API reference](references/api-reference.md) and
   optionally run `python scripts/mesh_io_probe.py --check-imports` or probe a
   specific file.
4. Decide material and heterogeneous-mesh policy before flattening, batching, or
   exporting.
5. For USD, confirm `pxr`, absolute scene paths, `time` handling, `up_axis`, and
   local-to-world transform conventions.
6. Route any post-load conversions, metrics, rendering, visualization, or
   physics work to the owning sub-skill with the normalized container contract.
