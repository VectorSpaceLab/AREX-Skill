---
name: tracking-core
description: "Use Norfair Detection and Tracker APIs for core multi-object
  tracking, distance selection, filters, lifecycle tuning, labels, embeddings,
  coordinate transforms, and ReID recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Tracking Core

Use this sub-skill when the task is to turn detector outputs into Norfair `Detection` objects, configure `Tracker`, choose a distance function, tune object lifecycle counters, use labels or embeddings, or recover identities after missed detections with ReID.

## Route here for

- Wrapping points, boxes, keypoints, scores, labels, extra data, or embeddings in `Detection`.
- Configuring `Tracker(...)`, `tracker.update(...)`, detection skip periods, coordinate-transform-aware tracking, and active-object retrieval.
- Choosing built-in distance names (`euclidean`, `iou`, `mean_euclidean`, `frobenius`, SciPy metrics) or writing a custom scalar distance callable.
- Selecting `OptimizedKalmanFilterFactory`, `FilterPyKalmanFilterFactory`, or `NoFilterFactory` and tuning filter noise/inertia parameters.
- Interpreting `TrackedObject` fields such as `id`, `global_id`, `estimate`, `estimate_velocity`, `age`, `hit_counter`, `point_hit_counter`, `live_points`, `last_detection`, `last_distance`, `past_detections`, and ReID counters.
- Using labels to prevent cross-class matches, storing embeddings on detections, and configuring `reid_distance_function`, `reid_distance_threshold`, and `reid_hit_counter_max`.
- Debugging core tracker data with `validate_points`, `get_cutout`, and `print_objects_as_table`.

## What this covers

- Core box, centroid, and keypoint tracking with a single Norfair `Tracker`.
- Distance families, from simple spatial metrics to custom scalar callables and normalized helpers.
- Tracker lifecycle controls: initialization delay, hit counters, point counters, and skipped-frame periods.
- Coordinate transforms for moving-camera tracking, including absolute vs relative estimates.
- ReID recovery using appearance embeddings and past detections.

## Typical workflow

1. Normalize detector outputs to NumPy arrays and wrap each object as `Detection`.
2. Pick the distance family from `references/workflows.md`: centroid/keypoint Euclidean, box IoU, normalized image-space distances, keypoint voting, or a custom scalar callable.
3. Construct `Tracker` with explicit `distance_threshold`, lifecycle thresholds, filter factory, and optional ReID parameters.
4. Feed frames in order with `tracker.update(detections=...)`; call `tracker.update()` on skipped/no-detection frames and pass `period` on frames where the detector ran after skipping.
5. Read returned active `TrackedObject` instances; inspect counters and past detections before changing thresholds.
6. If identity is lost after occlusion, add embeddings and ReID using `references/workflows.md#recover-tracks-after-occlusion-with-reid`, then diagnose with `references/troubleshooting.md`.

## Bundled scripts

- [`scripts/tracker_smoke.py`](scripts/tracker_smoke.py): safe tiny-fixture check for core tracking, labels, skipped frames, `validate_points`, `get_cutout`, object counters, and the tracker's NaN-distance guard.
- [`scripts/reid_smoke.py`](scripts/reid_smoke.py): pure NumPy synthetic same-label occlusion/ReID smoke adapted from the repository's ReID demo ideas without video files or source-tree dependencies.

## Route away

- Drawing detections/tracks, writing videos, OpenCV frame annotation, fixed-camera/path visualization, or camera-motion visualization: route to [video-visualization](../video-visualization/).
- MOTChallenge loading, metric computation, benchmark reports, or evaluation demo commands: route to [evaluation](../evaluation/).
- Detector-specific setup, model downloads, GPU inference demos, CLI help for demos, or training/fine-tuning detector models. This sub-skill starts after detector outputs are already available as arrays.

## Common signals to inspect

- The tracker returns no active objects even though detections exist.
- IDs flip after occlusion or when labels do not match.
- A custom distance returns `NaN` or a non-finite value.
- A moving-camera loop needs relative and absolute coordinates to stay consistent.
- A quick smoke check should prove the environment can update a tracker before any visualization or evaluation work.

Start with [workflows](references/workflows.md) for task recipes, [API reference](references/api-reference.md) for verified parameter behavior, and [troubleshooting](references/troubleshooting.md) when a tracker produces no active objects, ID switches, invalid-shape errors, or ReID failures.
