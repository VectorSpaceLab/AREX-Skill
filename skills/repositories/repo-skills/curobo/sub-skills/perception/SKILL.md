---
name: perception
description: "Builds cuRobo GPU TSDF/ESDF maps and sensor-observation pipelines
  for depth, LiDAR, feature grids, and pose-estimation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Perception and mapping

Use this route for `CameraObservation`/`LidarObservation`, depth filtering,
TSDF/ESDF mapping, lidar projection, occupied voxels, feature grids, and pose
estimation. Read [api-reference.md](references/api-reference.md) for contracts
and [mapping-workflows.md](references/mapping-workflows.md) for lifecycle.

## Core workflow

1. Define `MapperCfg` with `extent_meters_xyz`, TSDF/ESDF voxel sizes, depth
   limits, camera/lidar dimensions, and an explicit CUDA device. Keep the map
   small for a first synthetic check.
2. Build correctly shaped `CameraObservation` or `LidarObservation` tensors;
   filter invalid/out-of-range depth before integration and maintain camera
   intrinsics/extrinsics/projection rays.
3. Construct `Mapper`, integrate observations, call `compute_esdf()` when a
   collision/planning consumer needs distances, and inspect `get_stats()` or
   extracted voxels/mesh.
4. Use lidar projection and feature-grid options only when their dimensions,
   sensor count, and feature model are known. External datasets/models and
   Viser are optional and not part of the bounded core path.
5. Use [scripts/mapper_smoke.py](scripts/mapper_smoke.py) for a tiny synthetic
   CUDA lifecycle; never treat a downloaded dataset demo as a unit smoke.

Pass the resulting voxel/ESDF scene to [collision-scenes](../collision-scenes/SKILL.md)
or [motion-planning](../motion-planning/SKILL.md) only after coordinate frames
and voxel resolution are validated.
