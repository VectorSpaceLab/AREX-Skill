# Detection and Output Formats

## Detection tensors

BoxMOT selects the layout from the number of columns:

| Geometry | Input layout | Meaning |
| --- | --- | --- |
| AABB | `(N, 6)` | `(x1, y1, x2, y2, conf, cls)` |
| OBB | `(N, 7)` | `(cx, cy, w, h, angle, conf, cls)` |

The `angle` is in radians.

## Track outputs

| Geometry | Output layout | Meaning |
| --- | --- | --- |
| AABB | `(N, 8)` | `(x1, y1, x2, y2, id, conf, cls, det_ind)` |
| OBB | `(N, 9)` | `(cx, cy, w, h, angle, id, conf, cls, det_ind)` |

`det_ind` points back to the detection row that produced the track. A value of `-1` means the track is coasting or was not matched in that frame.

## `TrackResults` accessors

`TrackResults` is a NumPy view over the output tensor.

- `xyxy` exposes AABB coordinates
- `xywha` exposes OBB coordinates
- `id` returns integer track ids
- `conf` returns detection confidence scores
- `cls` returns integer class ids
- `det_ind` returns detection indices

## OBB geometry helpers

Useful helper facts from the runtime:

- `boxmot.trackers.common.geometry.obb.xywha_to_xyxy(...)` returns enclosing AABBs for oriented boxes.
- `smooth_display_angle(...)` keeps displayed OBB angle changes continuous.
- `align_obb_measurement(...)` chooses the candidate closest to the current state from the equivalent rectangle forms:
  - `(w, h, theta)`
  - `(w, h, theta + pi)`
  - `(h, w, theta + pi/2)`
  - `(h, w, theta - pi/2)`

## Detection-layout inference

`boxmot.trackers.common.detections.layout.infer_detection_layout(dets)` returns:

- AABB layout for 6-column detection tensors
- OBB layout for 7-column detection tensors
- `None` otherwise

The `BaseTracker` contract validates the shape before association runs.

## What to check when a user reports a bad shape

1. Confirm the detector is producing 6 or 7 columns.
2. Confirm the tracker supports OBB if the detections are oriented.
3. Confirm the downstream consumer is reading the correct result schema.
4. Check `det_ind` if the user needs to map tracks back to raw detections.
