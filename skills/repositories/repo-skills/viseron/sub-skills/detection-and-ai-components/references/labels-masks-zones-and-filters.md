# Labels, Masks, Zones, and Filters

Use this reference when a detector sees objects but Viseron does not record, store, publish, or post-process them as expected.

## Object detector per-camera shape

Object detector components share this per-camera shape under their `object_detector.cameras.<camera_identifier>` block:

```yaml
labels:
  - label: person
    confidence: 0.8
    trigger_event_recording: true
zones:
  - name: driveway
    coordinates:
      - {x: 100, y: 300}
      - {x: 900, y: 300}
      - {x: 900, y: 900}
      - {x: 100, y: 900}
    labels:
      - label: car
        confidence: 0.75
mask:
  - coordinates:
      - {x: 0, y: 0}
      - {x: 200, y: 0}
      - {x: 200, y: 1080}
      - {x: 0, y: 1080}
```

If neither `labels` nor `zones` is configured for a camera, Viseron creates the detector but logs that no objects will be detected.

## Label filters

A label entry tracks one object class from the model/service output. Available class names depend on the selected model and its label file; Viseron does not translate synonyms such as `vehicle` versus `car` unless the detector model produces that label.

Important object-label fields:

| Field | Default | Effect |
|---|---:|---|
| `label` | required | Exact object label to track. |
| `confidence` | `0.8` | Object must have confidence strictly greater than this value; equality fails the filter. |
| `width_min`, `width_max` | `0`, `1` | Relative object width must be strictly between min and max. |
| `height_min`, `height_max` | `0`, `1` | Relative object height must be strictly between min and max. |
| `trigger_event_recording` | `true` | Passing objects can start an event recording. Deprecated `trigger_recorder` maps to this behavior but should be replaced. |
| `store` | `true` | Passing objects are eligible for DB/snapshot storage. Objects that trigger a recording are stored at recording start even if normal store throttling would skip them. |
| `store_interval` | `60` | Seconds between storing repeat detections of the same label. `0` stores every detection. |
| `require_motion` | `false` | A recording that was triggered by this object should stop when motion stops; with no motion detector Viseron disables this requirement and logs a warning. |
| `require_motion_overlap` | `false` | The detected object's box must overlap motion contours before it can trigger/continue recording. Requires a motion detector to be meaningful. |
| `motion_overlap_threshold` | `0.1` | Fraction from `0` to `1` of the object's box that must be covered by motion contours when overlap is required. |

Detector-level `min_confidence` is different from per-label `confidence`. For example, `yolo.object_detector.min_confidence` filters raw YOLO predictions before Viseron's label filter is applied. Keep detector-level thresholds low enough that desired objects survive to label filtering.

## Zones

Zones define polygonal areas where you want to track one or more labels. A zone has a unique `name`, at least three coordinate points, and its own `labels`. Zone labels are independent from field-of-view labels; the same `person` label can have different confidence or recording behavior in the field of view and in a zone.

Viseron's zone test uses the horizontal middle of the object's lower edge. If that point is inside the zone polygon, the object is considered in the zone. This explains cases where a bounding box visibly overlaps a zone but does not count as inside because the lower-center point is outside.

Zone tips:

- Add labels inside every zone. A zone without labels exists but logs that no objects will be detected in that zone.
- Use zones to suppress sidewalk/road traffic while still keeping a broad field-of-view label for metadata if needed.
- Do not rely on zone names alone for recording; the zone label's `trigger_event_recording` controls event recordings for objects in the zone.
- Reuse exact model labels in zone labels; zone filters do not inherit labels from the top-level camera `labels` list.

## Masks

Masks are polygons that exclude areas before detection or post-processing:

- Motion detector masks ignore all movement inside the mask.
- Object detector masks are applied before inference/filtering. The user-facing rule is that an object whose lower portion is inside the mask is discarded.
- Post-processor masks apply to the frame before face, image-classification, or LPR processing.

Coordinate rules:

- Each polygon is a list of absolute pixel points with `x` and `y` integers.
- Each polygon needs at least three points.
- Coordinates should match the camera frame used by the detector, not a downscaled preview unless you also scale the points.
- Do not close a polygon by repeating the first point unless you intentionally want that redundant point; Viseron fills polygons from the provided point list.

Use [scripts/check_detection_config.py](../scripts/check_detection_config.py) to catch too-short polygons and non-numeric coordinates in YAML/JSON snippets.

## Motion overlap and object scanning gates

These settings often explain "object detected but recording did not start":

1. `scan_on_motion_only: true` means object detection scans only while motion is active when a motion detector is registered. Without a motion detector, Viseron disables this gate and logs a warning.
2. `require_motion_overlap: true` means a detected object must overlap motion contours enough to pass `motion_overlap_threshold`. The NVR keeps scanner motion active when overlap is required so contours can be produced.
3. If a motion detector exists and motion is false, overlap-required objects do not trigger recording.
4. If motion is true but no usable contours are available, Viseron's overlap helper treats the object as passing the overlap check. This can happen for external motion sources or scanner states without contour data.
5. If no motion detector is configured, `require_motion` is disabled with a warning and `require_motion_overlap` is not effective.

## Recording decision checklist

When a user says "the detector sees a person but Viseron does not record", inspect in this order:

1. Does the detector model output exactly the configured `label`?
2. Is the object confidence strictly greater than both the detector-level threshold and the label `confidence`?
3. Are `width_min`/`width_max` and `height_min`/`height_max` excluding the box?
4. Is an object mask covering the object's lower portion?
5. If the label is only under a zone, is the object's lower-center point inside that zone, and does that zone label set `trigger_event_recording: true`?
6. If `scan_on_motion_only` is true, was motion active at the time the object detector should have scanned?
7. If `require_motion` or `require_motion_overlap` is true, is a motion detector configured for the same camera, and are motion contours overlapping enough?
8. Is event recording allowed by the camera/NVR schedule and recorder settings? If this question moves beyond detector filters, route to `camera-recording-pipeline`.
9. Is `trigger_event_recording` false because the label is intended for metadata or post-processing only?
10. Are objects being throttled by `store_interval` rather than missing? Recording and database/snapshot storage are related but not identical.
