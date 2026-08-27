---
name: camera-and-segmentation
description: "Guides Waymo Open Dataset camera custom ops, camera-only
  detection, PVPS, semantic segmentation, E2E driving data, and optional
  Deeplab2 camera segmentation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Camera and Segmentation

Use this sub-skill for WOD camera model/custom ops, camera-only 3D detection, 2D panoramic video panoptic segmentation (PVPS), 3D semantic segmentation, camera segmentation metrics, E2E driving data/submission protos, WDL-limited camera code, and `deeplab2`/compiled-op troubleshooting.

Read:

- [references/api-reference.md](references/api-reference.md) for camera/segmentation utility surfaces and optional dependency status.
- [references/workflows.md](references/workflows.md) for camera-only detection, PVPS, semantic segmentation, and E2E driving outlines.
- [references/data-formats.md](references/data-formats.md) for camera, segmentation, and E2E proto expectations.
- [references/troubleshooting.md](references/troubleshooting.md) for Deeplab2, WDL-limited licenses, camera names, custom op imports, and dataset prerequisites.

Run [`scripts/check_camera_segmentation_imports.py`](scripts/check_camera_segmentation_imports.py) to report camera op and Deeplab2 availability.

Route v1 camera image extraction to `dataset-utils`, V2 camera Parquet components to `v2-components`, and generic metric wrapper mechanics to `metrics-evaluation`.
