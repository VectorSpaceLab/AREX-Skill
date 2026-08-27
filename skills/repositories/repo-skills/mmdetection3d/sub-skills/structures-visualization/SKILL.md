---
name: structures-visualization
description: "Work with MMDetection3D box, point, coordinate-conversion, and
  visualization geometry."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDetection3D structures and visualization sub-skill

Use this sub-skill for:
- 3D box origin, yaw, and mode questions.
- LiDAR / Camera / Depth box and point conversions.
- `points_cam2img` / `points_img2cam` projection checks.
- `Det3DLocalVisualizer` and saved geometry artifacts from demos or evaluation.

## Start here

1. Identify the coordinate family and whether the object is a box, point cloud, or image projection artifact.
2. Use [`references/geometry-api.md`](references/geometry-api.md) for origin, yaw, mode, and projection rules.
3. Use [`references/visualization.md`](references/visualization.md) for visualizer methods and saved-output conventions.
4. Run [`scripts/inspect_geometry.py`](scripts/inspect_geometry.py) for a tiny synthetic smoke check when the installed package is available.
5. Use [`references/troubleshooting.md`](references/troubleshooting.md) when a box looks shifted, mirrored, clipped, or empty.

## Route away

- End-to-end inference and prediction outputs belong in `inference`.
- Dataset browsing or conversion belongs in `data-preparation`.
- Training, testing, TTA, or distributed launch belongs in `training-evaluation`.
- Config choice or adaptation belongs in `configuration-model-zoo`.

## Operating rules

- Treat box origin as part of the data contract.
- Keep LiDAR, Camera, and Depth modes explicit in every conversion.
- Prefer bundled references and script output over source-repo paths.
- Do not rely on GUI display during the smoke check.
