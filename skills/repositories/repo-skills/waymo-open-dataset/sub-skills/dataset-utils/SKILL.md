---
name: dataset-utils
description: "Guides Waymo Open Dataset v1 Frame protos, range-image parsing,
  point clouds, camera projections, geometry, maps, and keypoint utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dataset Utils

Use this sub-skill when the task is about v1 WOD `Frame` protos, TFRecord frame parsing, compressed range images, range-image-to-point-cloud conversion, camera projections, map features, geometry transforms, 2D/3D boxes, or keypoint helper data.

Read:

- [references/api-reference.md](references/api-reference.md) for verified signatures and call order.
- [references/data-formats.md](references/data-formats.md) for Frame, lidar/camera arrays, point cloud outputs, and keypoint structures.
- [references/workflows.md](references/workflows.md) for Frame-to-point-cloud, map, and keypoint recipes.
- [references/troubleshooting.md](references/troubleshooting.md) for decompression, TensorFlow eager, calibration, shape, and empty-output failures.

Run [`scripts/check_frame_utils_imports.py`](scripts/check_frame_utils_imports.py) to check installed import/signature availability without downloading data.

Route elsewhere for V2 Parquet components (`v2-components`), metric scoring (`metrics-evaluation`), WOMD/sim-agent challenge workflows (`motion-sim-agents`), or camera custom-op/challenge segmentation (`camera-and-segmentation`).
