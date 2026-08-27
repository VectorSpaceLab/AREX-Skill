# Tracking and keypoint workflows

Use this reference after the router chooses the tracking-keypoints sub-skill. It
summarizes the keypoint container, keypoint annotators, conversion to
`Detections`, tracker-ID flows, and deprecated-path migration rules for
`supervision` `0.31.0.dev0`.

## KeyPoints container contract

`sv.KeyPoints` stores one row per detected object and one column per keypoint in
that object's skeleton.

| Field | Shape | Meaning and operating notes |
| --- | --- | --- |
| `xy` | `(n, m, 2)` or `(n, m, 3)` | Required coordinates. Most workflows use the first two coordinates. All-zero anchors are commonly used by model adapters to mean missing keypoint. |
| `class_id` | `(n,)` or `None` | Per-skeleton class IDs. Required for class-aware `with_nms(...)` and for per-class edge/label dictionaries. |
| `keypoint_confidence` | `(n, m)` or `None` | Per-anchor scores. This replaces the deprecated `confidence` field/property. |
| `detection_confidence` | `(n,)` or `None` | Per-skeleton confidence. Preferred by `as_detections()` and required by `with_nms(...)`. |
| `visible` | `(n, m)` boolean array or `None` | Per-anchor visibility mask. When `None`, annotators treat anchors as visible, while all-zero coordinates are still skipped by keypoint rendering. |
| `data` | dict of arrays/lists length `n` | Extra per-skeleton metadata such as `class_name` or `covariance`. Values must stay aligned with `xy`. |

Constructor guardrails:

- `xy` must be 3-D and each optional per-skeleton/per-keypoint field must match
  the row/keypoint counts.
- `data=None` normalizes to `{}`.
- Passing both `confidence=` and `keypoint_confidence=` raises. Passing only
  `confidence=` still maps to `keypoint_confidence` with a deprecation warning;
  new code should not use it.
- `KeyPoints.confidence` is a deprecated property alias for
  `KeyPoints.keypoint_confidence` and is scheduled for removal after this target
  version family.

## Constructors and adapters

| API | Use it when | Important notes |
| --- | --- | --- |
| `sv.KeyPoints(xy=..., class_id=..., keypoint_confidence=..., detection_confidence=..., visible=..., data=...)` | You already have normalized NumPy arrays. | Use `np.float32` coordinates/scores and `np.ndarray` optional fields. |
| `sv.KeyPoints.empty()` | No keypoints are present. | Returns `xy` shape `(0, 0, 2)`; `len(...) == 0`. |
| `sv.KeyPoints.merge(list_of_key_points)` | Combining batches with identical skeleton schemas. | Empty inputs are ignored. Non-empty inputs must agree on keypoint count, coordinate depth, optional-field presence, and `data` keys. |
| `sv.KeyPoints.from_ultralytics(result)` | YOLO pose result object. | Reads `keypoints.xy`, `keypoints.conf`, boxes classes, and class names. Requires the model package in the caller environment. |
| `sv.KeyPoints.from_inference(result)` | Roboflow Inference pose result. | Pass one result at a time, not a list. Stores class names under `data["class_name"]`. |
| `sv.KeyPoints.from_mediapipe(result, resolution_wh=(width, height))` | MediaPipe pose or face landmarks. | Scales normalized landmarks to pixels. Supports modern and legacy pose/face result shapes. |
| `sv.KeyPoints.from_yolo_nas(result)` | YOLO-NAS pose output. | Handles optional labels/class names when present. |
| `sv.KeyPoints.from_detectron2(result)` | Detectron2 instances with predicted keypoints. | Returns empty when `pred_keypoints` is absent or empty. |
| `sv.KeyPoints.from_transformers(result)` | Transformers pose-estimation post-processing output. | Returns empty when no `keypoints` field is present. |

Model/framework packages are outside the base `pip install supervision` runtime.
Import or install only the adapter dependency that the user's model output
actually needs.

## Filtering, indexing, and NMS

`KeyPoints` mirrors many `Detections` selection patterns:

```python
import numpy as np
import supervision as sv

key_points = sv.KeyPoints(
    xy=np.array([[[10, 20], [30, 40]], [[100, 120], [0, 0]]], dtype=np.float32),
    keypoint_confidence=np.array([[0.9, 0.8], [0.7, 0.0]], dtype=np.float32),
    detection_confidence=np.array([0.95, 0.60], dtype=np.float32),
    class_id=np.array([0, 0], dtype=int),
)

high_conf_skeletons = key_points[key_points.detection_confidence > 0.7]
first_anchor_for_all = key_points[:, 0]
class_names = key_points["class_name"]  # returns data value or None
```

Selection rules to remember:

- A row mask such as `key_points[key_points.class_id == 0]` filters skeletons.
- A column selection such as `key_points[:, [0, 1, 2]]` selects the same anchor
  indices from every skeleton.
- A 2-D boolean mask is allowed only when each row selects the same number of
  `True` values. For per-object confidence filtering that would create ragged
  skeletons, prefer `key_points.visible = key_points.keypoint_confidence > t`
  rather than deleting anchors.
- `KeyPoints.merge(...)` is useful before `with_nms(...)` when multiple pose
  sources share one skeleton schema.

`KeyPoints.with_nms(threshold=0.5, class_agnostic=False, overlap_metric=...)`
performs box NMS using boxes derived from non-zero, visible keypoints. It
requires `detection_confidence`; class-aware mode also requires `class_id`.
Choose `class_agnostic=True` when different class IDs should still suppress each
other.

## Keypoint annotators

All keypoint annotators follow the familiar `.annotate(scene, key_points)` shape
and return the annotated scene. NumPy scenes use OpenCV-style BGR channel order;
PIL images are accepted by these annotators and converted internally.

| Annotator | Purpose | Key parameters and traps |
| --- | --- | --- |
| `sv.VertexAnnotator` | Draw circular vertices. | `color`, `radius`. Skips all-zero anchors and anchors where `visible` is `False`. |
| `sv.EdgeAnnotator` | Draw skeleton edges. | `edges=None` auto-detects by vertex count; custom edges use 1-based indices. A dict maps `class_id` to edge lists and requires `key_points.class_id`. |
| `sv.VertexLabelAnnotator` | Draw per-keypoint labels. | `labels=None` uses numeric indices. A list applies to all skeletons; a dict maps `class_id` to label lists. Label/color lists must match keypoint count. |
| `sv.VertexEllipseAreaAnnotator` | Filled covariance ellipses. | Requires `key_points.data["covariance"]` with shape `(n, m, 2, 2)`. Supports sigma/color sequences and `max_axis`. |
| `sv.VertexEllipseOutlineAnnotator` | Stroke-only covariance ellipses. | Same covariance requirement. Use `thickness` for outlines. |
| `sv.VertexEllipseHaloAnnotator` | Soft halo covariance ellipses. | Same covariance requirement. Useful when uncertainty should be visually prominent. |
| `sv.VertexEllipseAnnotator` | Compatibility alias. | Alias for `VertexEllipseAreaAnnotator`; prefer the explicit area/outline/halo class in new explanations. |

Example composition:

```python
import numpy as np
import supervision as sv

key_points.visible = key_points.keypoint_confidence > 0.3

edge_annotator = sv.EdgeAnnotator(edges=[(1, 2), (2, 3)])
vertex_annotator = sv.VertexAnnotator(radius=5)

annotated = edge_annotator.annotate(scene=frame.copy(), key_points=key_points)
annotated = vertex_annotator.annotate(scene=annotated, key_points=key_points)
```

For non-keypoint boxes, masks, labels, traces, heatmaps, or color strategy,
route to [annotators](../../annotators/SKILL.md) unless tracker IDs are central.

## Keypoints to detections

Tracking and many zone/trace workflows operate on `sv.Detections`, not directly
on `sv.KeyPoints`. Convert keypoints to detection boxes with:

```python
detections = key_points.as_detections(
    selected_keypoint_indices=[5, 6, 11, 12],
)
```

Conversion behavior:

- The box is the min/max rectangle around the selected keypoints, or all
  keypoints when `selected_keypoint_indices` is `None` or an empty iterable.
- All-zero anchors and non-finite anchors are ignored for box construction.
- Skeletons with no valid keypoints are filtered out and their metadata is
  filtered with them.
- Valid single-keypoint or collinear skeletons remain as zero-area detections.
  Those may be useful for inspection but are not good tracker inputs because the
  bundled ByteTrack compatibility wrapper drops zero-width or zero-height boxes.
- `detections.confidence` is `detection_confidence` when present; otherwise it
  is the mean of the selected `keypoint_confidence`; otherwise it is `None`.
- `class_id` and `data` are preserved and aligned. `tracker_id` is not created by
  conversion; a tracker must assign it later.

A robust keypoint-to-tracking preparation flow:

```python
import numpy as np
import supervision as sv

key_points = sv.KeyPoints.from_ultralytics(result)
key_points.visible = key_points.keypoint_confidence > 0.3

if key_points.detection_confidence is not None and key_points.class_id is not None:
    key_points = key_points.with_nms(threshold=0.5)

detections = key_points.as_detections(selected_keypoint_indices=[5, 6, 11, 12])
if detections.confidence is None:
    raise ValueError("Tracking requires detection confidence scores")
```

Use [detection-and-zones](../../detection-and-zones/SKILL.md) for pure detection
filtering, sinks, or zone geometry after the conversion.

## Tracker-ID workflows and ByteTrack migration

Persistent identity is carried by `detections.tracker_id`. The tracker should be
called once per video frame, in frame order, and reset between independent video
streams.

Prefer the external tracker when the user can install it:

```python
try:
    from trackers import ByteTrackTracker
except ImportError:
    ByteTrackTracker = None

if ByteTrackTracker is not None:
    tracker = ByteTrackTracker()
    update_tracks = tracker.update
else:
    tracker = sv.ByteTrack()  # deprecated compatibility fallback
    update_tracks = tracker.update_with_detections

detections = update_tracks(detections)
```

Migration facts:

- `sv.ByteTrack` is deprecated in this target. It may still be lazily available
  as `sv.ByteTrack`, but answers should recommend migrating to the external
  `ByteTrackTracker` package.
- The external tracker's update method is named `update(...)`; the deprecated
  supervision wrapper uses `update_with_detections(...)`.
- Old wrapper parameters `track_thresh`, `track_buffer`, and `match_thresh` are
  not current. Use `track_activation_threshold`, `lost_track_buffer`, and
  `minimum_matching_threshold` for the compatibility wrapper.
- `sv.ByteTrack.update_with_detections(...)` requires `detections.confidence` and
  does not mutate the input detections. It returns a copy containing only matched
  tracked detections with `tracker_id` assigned.
- The wrapper drops invalid, non-finite, zero-width, or zero-height boxes before
  Kalman updates.
- `frame_rate` scales the lost-track buffer; pass the real video FPS when known.
- `minimum_consecutive_frames > 1` delays ID emission. The first frame may return
  no tracks even with detections, which is expected.

Tracker output is the input for identity-dependent rendering and counting:

```python
class_names = detections.data.get("class_name")
if class_names is None:
    labels = [f"#{tracker_id}" for tracker_id in detections.tracker_id]
else:
    labels = [
        f"#{tracker_id} {class_name}"
        for tracker_id, class_name in zip(detections.tracker_id, class_names)
    ]

annotated = sv.BoxAnnotator().annotate(scene=frame.copy(), detections=detections)
annotated = sv.LabelAnnotator().annotate(
    scene=annotated,
    detections=detections,
    labels=labels,
)
annotated = sv.TraceAnnotator().annotate(scene=annotated, detections=detections)
```

If class names are absent, build labels from `class_id` or just from
`tracker_id`. Check [troubleshooting.md](troubleshooting.md) before adding custom
state around trace or line-zone failures.

## LineZone and tracker-dependent counting

`sv.LineZone` counts crossings over time, so it needs stable `tracker_id` values.
Without IDs, `LineZone.trigger(...)` returns all-False arrays and emits a
warning; it does not invent identities.

```python
line_zone = sv.LineZone(
    start=sv.Point(100, 200),
    end=sv.Point(500, 200),
    triggering_anchors=[sv.Position.BOTTOM_CENTER],
    minimum_crossing_threshold=2,
)

crossed_in, crossed_out = line_zone.trigger(detections)
```

Important behavior:

- `triggering_anchors` controls which box anchors are tested against the line.
  A bottom-center anchor is often better for people or vehicles than all four
  corners.
- `minimum_crossing_threshold` requires the detection to remain on the other
  side of the line for more frames, reducing jitter counts.
- Empty frames and absent tracker IDs eventually evict crossing history. Short
  tracker gaps do not immediately reset line state.
- Per-class counts are keyed by current `class_id`, but crossing history remains
  continuous for the same `tracker_id` across class flicker.

Use [detection-and-zones](../../detection-and-zones/SKILL.md) when the task is
only about geometry, polygon membership, or zone rendering. Stay here when the
question is about missing IDs, ID continuity, tracker thresholds, or line counts.

## Optional polygon-zone authoring helper

This sub-skill bundles an adapted interactive helper at
[draw_zones.py](../scripts/draw_zones.py). It lets a user click polygon vertices
on an image or first video frame and save JSON polygon coordinates. It has no
model, network, or credential dependency, but it requires a GUI-capable desktop
session and an OpenCV-compatible drawing/video backend.
