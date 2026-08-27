---
name: ops-metrics-conversions
description: "Batching, representation conversions, SPC, Gaussian, quaternion,
  and metric workflows for Kaolin tensors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ops-metrics-conversions

Use this sub-skill for in-memory Kaolin work where geometry is already a tensor or Kaolin container and the task is about tensor batching, operations, conversions, math, or metrics.

## Use when

- Choosing list, exact, packed, or padded layout for variable-size 3D tensors.
- Sampling/inspecting triangle meshes, point clouds, voxelgrids, SPC octrees, or Gaussian tensors.
- Converting among mesh, pointcloud, voxelgrid, SPC, and Gaussian occupancy representations.
- Applying `kaolin.math.quat` quaternion, rotation, Euclidean, or compact transform helpers.
- Computing pointcloud, point-to-mesh, voxelgrid, mask, or mesh-regularization metrics/losses.

## Route elsewhere

- File I/O, datasets, `SurfaceMesh` construction, materials, USD/OBJ/PLY/GLTF/container selection: `geometry-io-representations`.
- Cameras, lighting, rasterization, differentiable rendering, ray tracing, images: `rendering-cameras-lighting`.
- Simplicits/Newton/Warp simulation loops and training-state physics: `physics-simulation`.
- Timelapse, Dash3D, notebooks, browser/WebGL display: `visualization-workflows`.

## Read first

- [API reference](references/api-reference.md) for function names, shape contracts, and backend gates.
- [Workflows](references/workflows.md) for layout selection, conversions, Gaussian transforms, quaternion recipes, and metric choices.
- [SPC workflows](references/spc-workflows.md) for octree, `lengths`, `pyramids`, `exsum`, query/interpolation, and convolution conventions.
- [Troubleshooting](references/troubleshooting.md) for packed/padded, CPU/CUDA, Warp, SPC `lengths`, and legacy/current `exsum` failures.

## Bundled probes

- [Quaternion smoke](scripts/quaternion_smoke.py): CPU-safe quaternion/transform round trips.
- [Tensor ops smoke](scripts/tensor_ops_smoke.py): CPU tensor, mesh, voxel, Gaussian-transform, metric checks; optional `--cuda-smoke` for CUDA/SPC paths.

## Operating rules

1. Keep layout explicit: list, exact batch, packed, padded, dense voxelgrid, sparse SPC, per-face feature, or per-point feature.
2. Prefer packed layouts when element counts vary and downstream code supports flattened indexing; use padded layouts only when dense batch axes are required.
3. Carry `shape_per_tensor`, `numel_per_tensor`, and `first_idx` with packed data.
4. For SPC `scan_octrees`, keep `lengths` on CPU and prefer the current `exsum` layout from `scan_octrees(octrees, lengths)`.
5. `kaolin.math.quat` uses xyzw quaternions; `transform_gaussians` defaults to wxyz unless `use_xyzw=True`.
6. Gate CUDA-only operations explicitly; a CPU import is not proof that SPC, marching-cubes, Gaussian voxelization, or pointcloud metric kernels are available.
