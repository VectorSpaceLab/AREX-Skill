---
name: tracking-keypoints
description: "Operate supervision keypoint containers, keypoint annotators,
  tracking IDs, and migration paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tracking Keypoints

Use this sub-skill when a task involves `supervision` keypoint data, keypoint
annotation, keypoint-to-detection conversion for tracking, persistent
`tracker_id` workflows, line-crossing/counting that depends on tracker identity,
or migration away from deprecated keypoint/tracker APIs.

## Route here for

- `KeyPoints`, `keypoint_confidence`, `detection_confidence`, `visible`,
  `KeyPoints.merge`, `KeyPoints.with_nms`, and `KeyPoints.as_detections`.
- Keypoint adapters such as `KeyPoints.from_ultralytics`, `from_inference`,
  `from_mediapipe`, `from_yolo_nas`, `from_detectron2`, and
  `from_transformers`.
- `VertexAnnotator`, `EdgeAnnotator`, `VertexLabelAnnotator`,
  `VertexEllipseAreaAnnotator`, `VertexEllipseOutlineAnnotator`,
  `VertexEllipseHaloAnnotator`, and the `VertexEllipseAnnotator` alias.
- `ByteTrack`, `ByteTrackTracker`, `tracker_id`, `track_objects`, track labels,
  `TraceAnnotator`, `DetectionsSmoother`, and `LineZone` when persistent
  identity is central to the answer.
- Deprecated `supervision.keypoint`, deprecated `sv.ByteTrack`, old ByteTrack
  threshold names, and the `KeyPoints.confidence` rename.

## Route away

- Build, filter, save, or reason about ordinary `Detections`, masks, polygon
  zones, line-zone geometry, sinks, or slicers when tracker continuity is not
  central: use [detection-and-zones](../detection-and-zones/SKILL.md).
- Non-keypoint detection/mask/label visualization and annotator catalog choices:
  use [annotators](../annotators/SKILL.md).
- Image/video I/O, primitive drawing, OpenCV backend diagnosis, GUI/window
  problems, and video codecs: use [media-utils](../media-utils/SKILL.md).
- Dataset conversion or detection metric evaluation: use the corresponding
  dataset or metrics sub-skill.

## Operating checklist

1. Identify the active container. Pose/keypoint model outputs should become
   `sv.KeyPoints`; tracking, line crossing, traces, smoothing, and most labels
   operate on `sv.Detections` with `tracker_id`.
2. Prefer `sv.KeyPoints` or `supervision.key_points`. Do not introduce new
   `supervision.keypoint` imports; that path is compatibility-only and scheduled
   for removal.
3. Use `keypoint_confidence` for per-anchor scores and `detection_confidence`
   for whole-skeleton scores. Treat `KeyPoints.confidence` and `confidence=` as
   deprecated compatibility shims.
4. Before keypoint annotation, decide whether missing/weak anchors should be
   hidden with `key_points.visible`. When `visible` is `None`, annotators treat
   anchors as visible except that all-zero coordinates are skipped.
5. Before keypoint tracking, convert with `key_points.as_detections(...)`, ensure
   the resulting detections have confidence scores and positive-area boxes, then
   run a tracker. Prefer the external `ByteTrackTracker` package when available;
   `sv.ByteTrack` is only a deprecated compatibility fallback in this version.
6. Use the tracked `Detections` object for tracker labels, traces, detection
   smoothing, and `LineZone.trigger(...)`. Missing `tracker_id` is the first
   thing to check when these workflows do nothing or raise.
7. Put detailed API choices and recipes in
   [tracking-keypoints.md](references/tracking-keypoints.md), and failure repair
   steps in [troubleshooting.md](references/troubleshooting.md). Use the bundled
   [draw_zones.py](scripts/draw_zones.py) helper only for interactive polygon
   authoring in a GUI-capable environment.

## Required context to keep in answers

- Target package facts: `supervision` `0.31.0.dev0`, Python `>=3.10`, base
  install `pip install supervision`.
- Model adapters require their own model/framework packages; they are not part
  of the base `supervision` install.
- `ByteTrackTracker` comes from the optional external `trackers` package.
  `sv.ByteTrack` still exists as a lazy compatibility export in this target, but
  it is deprecated and should not be presented as stable.
- Native OpenCV is optional for the package. Interactive helpers require a GUI
  display and an OpenCV-compatible drawing/video backend; the documented
  fallback backend may render or decode differently from native OpenCV.
- Do not recommend original repository docs, examples, tests, scripts, local
  checkout paths, or generated skill import steps as runtime dependencies.
