# Tracking-keypoints troubleshooting

Start here when keypoint rendering, conversion, tracking, traces, or line-zone
counts fail. Most issues come from deprecated imports, misaligned `KeyPoints`
fields, missing visibility masks, missing detection confidence, or missing
`tracker_id` after conversion.

## Deprecated imports and renamed fields

| Symptom | Likely cause | Repair |
| --- | --- | --- |
| Warning about `supervision.keypoint` | Old module path is used. | Replace with `sv.KeyPoints`/top-level annotators or `supervision.key_points`. Do not add new `supervision.keypoint` imports. |
| Warning about `KeyPoints.confidence` or `confidence=` | Legacy per-keypoint confidence alias. | Use `keypoint_confidence=` and read `key_points.keypoint_confidence`. Keep `detection_confidence` separate. |
| `sv.ByteTrack` warning | Built-in wrapper is deprecated. | Prefer `ByteTrackTracker` from the optional `trackers` package and call `update(...)`. Use `sv.ByteTrack.update_with_detections(...)` only as a compatibility fallback for this target. |
| Old ByteTrack args fail | Removed names such as `track_thresh`, `track_buffer`, `match_thresh`. | Use `track_activation_threshold`, `lost_track_buffer`, and `minimum_matching_threshold`. |

The target version still exposes some deprecated compatibility paths, but they
are removal risks. Answers should migrate code rather than normalizing the old
paths as stable API.

## KeyPoints construction errors

Check the array contract before debugging model output:

- `xy` must be a 3-D `np.ndarray` with shape `(n, m, 2)` or `(n, m, 3)`.
- `class_id` must be `None` or shape `(n,)`.
- `keypoint_confidence` must be `None` or shape `(n, m)`.
- `detection_confidence` must be `None` or shape `(n,)`.
- `visible` must be `None` or a 2-D boolean array with shape `(n, m)`.
- Each `data` value must be a list/array aligned to the `n` skeleton rows.
- `data=None` is fine and becomes an empty dict.

If a model produces one object at a time, keep the leading object dimension:
`xy` should be shaped like `(1, m, 2)`, not `(m, 2)`.

## Missing visible masks or invisible anchors

When `visible` is `None`, `VertexAnnotator`, `EdgeAnnotator`, and
`VertexLabelAnnotator` treat anchors as visible, but all-zero coordinates are
still skipped. If weak anchors are being drawn, create a visibility mask instead
of deleting per-object anchors:

```python
if key_points.keypoint_confidence is not None:
    key_points.visible = key_points.keypoint_confidence > 0.3
```

Do not filter multi-object keypoints with a per-anchor confidence mask when each
skeleton would keep a different number of anchors. `KeyPoints` stores a regular
array, not ragged skeletons. Use `visible` for per-object hiding, or select a
fixed anchor subset with `key_points[:, [0, 1, 2]]`.

## Edge and label annotator failures

- Custom `EdgeAnnotator(edges=...)` edges use a 1-based convention. `(1, 2)` is
  valid for the first two keypoints; `(0, 1)` is not.
- When `edges` is a dict, `key_points.class_id` must be set and every rendered
  class must have an entry.
- When `VertexLabelAnnotator(labels=...)` receives a dict, `class_id` must be
  set and every class must have a label list.
- Label and color lists must have the same length as the skeleton's keypoint
  count.
- Ellipse annotators require `key_points.data["covariance"]` with shape
  `(n, m, 2, 2)`. Invalid covariance shape, non-finite values, or non-positive
  eigenvalues result in errors or skipped ellipses.
- If a scene type is rejected, make sure it is a NumPy image or PIL image. NumPy
  images should be `uint8` in BGR order for OpenCV-style rendering.

## `with_nms(...)` raises or suppresses unexpectedly

`KeyPoints.with_nms(...)` derives boxes from valid non-zero, visible keypoints.
It is not the same as point-wise confidence filtering.

- `detection_confidence` is required. If only per-keypoint confidence exists,
  decide a whole-skeleton score before NMS or convert with `as_detections()` and
  use detection-level filtering there.
- Class-aware NMS (`class_agnostic=False`) also requires `class_id`.
- `class_agnostic=True` suppresses overlapping skeletons across classes.
- A hidden endpoint can shrink the derived NMS box. If NMS behaves oddly, inspect
  `visible` and all-zero anchors first.

## `as_detections(...)` output surprises

| Surprise | Explanation and repair |
| --- | --- |
| Fewer detections than keypoint skeletons | Skeletons with no valid keypoints after selected-index filtering are removed. All-zero and non-finite anchors are invalid for box construction. |
| Zero-area boxes remain | A valid single keypoint or collinear keypoints produce a valid degenerate box. This is useful for inspection but poor for ByteTrack, which ignores zero-width/zero-height boxes. Choose a keypoint subset that spans area, pad boxes intentionally, or avoid tracking that skeleton. |
| Confidence is unexpected | `detection_confidence` wins. If absent, the mean of selected `keypoint_confidence` columns is used. If both are absent, `detections.confidence` is `None`. |
| Empty `selected_keypoint_indices=[]` does not select nothing | Empty selected-index iterables are treated like `None` and select all keypoints. |
| `tracker_id` is still missing | Conversion does not track. Run a tracker after conversion and use the tracked detections returned by the tracker. |

Before passing converted detections to a tracker, assert the two essentials:

```python
import numpy as np

if detections.confidence is None:
    raise ValueError("Tracker requires Detections.confidence")
if len(detections) and np.any(detections.xyxy[:, 2:] <= detections.xyxy[:, :2]):
    raise ValueError("Tracker input contains zero-area or negative-area boxes")
```

## No tracker output or unstable tracker IDs

For the deprecated `sv.ByteTrack` compatibility wrapper:

- `update_with_detections(...)` requires `detections.confidence`.
- Non-finite boxes, zero-width boxes, and zero-height boxes are dropped.
- `track_activation_threshold` controls which detections can start tracks.
  Raising it reduces false tracks but can miss real objects.
- The implementation still uses low-confidence detections above `0.1` for
  second-stage association, which can improve continuity but may keep noisy
  tracks alive.
- `minimum_matching_threshold` controls association strictness. Lower values can
  reduce drift but increase fragmentation; higher values can keep tracks through
  looser matches but risks identity switches.
- `lost_track_buffer` is scaled by `frame_rate`. Pass the actual video FPS when
  known; a wrong FPS changes how long lost tracks coast.
- `minimum_consecutive_frames > 1` delays ID emission. Empty output on the first
  frame can be expected.
- Call `tracker.reset()` before processing an independent video. Reusing a
  tracker across unrelated streams carries old state.

When using the external `ByteTrackTracker`, call `update(...)`, not
`update_with_detections(...)`, and verify its constructor options in the user's
installed package version.

## Labels, traces, smoothing, or LineZone complain about `tracker_id`

These workflows must consume the detections returned by the tracker, not the raw
model detections and not the pre-tracking keypoint conversion.

- `LabelAnnotator` itself can draw arbitrary labels, but labels such as
  `f"#{tracker_id}"` require `detections.tracker_id` to be present and aligned.
- `TraceAnnotator` raises when `tracker_id` is missing. Its `smooth=True` path
  handles stationary trackers by falling back to a raw polyline when there are
  too few unique points.
- `DetectionsSmoother.update_with_detections(...)` warns and returns unchanged
  detections when `tracker_id` is missing.
- `LineZone.trigger(...)` warns and returns all-False crossing arrays when
  `tracker_id` is missing.

A quick guard is:

```python
detections = update_tracks(detections)
if detections.tracker_id is None:
    raise ValueError("Tracking did not assign tracker_id")
```

## LineZone counts are missing or double counted

- Confirm the same physical object keeps the same `tracker_id` across frames.
  Line crossing is impossible to count reliably without persistent IDs.
- Use `triggering_anchors` that match the task. For people/vehicles,
  `Position.BOTTOM_CENTER` often counts entry more intuitively than all corners.
- Increase `minimum_crossing_threshold` when boxes jitter around the line. This
  requires more consecutive evidence on the other side before counting.
- Empty frames and absent IDs are tolerated briefly, then crossing history is
  evicted. Long detection gaps can reset line state.
- Per-class counts use the current `class_id`, while crossing history is keyed by
  `tracker_id`; class flicker should not by itself reset the crossing history.

Route line geometry, polygon zones, and zone rendering to
[detection-and-zones](../../detection-and-zones/SKILL.md) unless the bug is about
tracker identity or count continuity.

## `draw_zones.py` helper issues

The bundled [draw_zones.py](../scripts/draw_zones.py) script is intentionally
small and interactive. It is adapted for polygon-zone authoring only.

- It requires `supervision`, NumPy, a GUI-capable desktop session, and a working
  display. On headless servers, the window may fail before any drawing happens.
- It uses `sv.ImageWindow`, which relies on tkinter/Pillow for the window and an
  OpenCV-compatible backend for image/video loading and drawing. Native OpenCV
  can improve video compatibility, but the documented fallback backend may work
  for simple image cases.
- It loads an image or the first frame of a video; it does not run inference,
  download models, or open streams.
- Controls: left-click adds vertices, `Return`/`KP_Enter` closes the current
  polygon, `Escape` clears the unfinished polygon, `s` saves JSON, and `q` quits
  without saving.
- The saved JSON is a list of polygons, where each polygon is a list of `[x, y]`
  coordinate pairs. Incomplete polygons with fewer than three vertices are not
  saved.

For media backend, codec, Tk, or display diagnosis, route to
[media-utils](../../media-utils/SKILL.md).
