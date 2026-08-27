# Tracking Workflows

Use these recipes for core tracking tasks. They assume detector outputs are already available as NumPy arrays or arrays convertible to NumPy.

## 1) Wrap detector outputs into `Detection`

```python
import numpy as np
from norfair.tracker import Detection

raw_points = np.array([[10.0, 20.0], [12.0, 24.0]], dtype=float)
raw_scores = np.array([0.95, 0.88], dtype=float)

norfair_detection = Detection(
    points=raw_points,
    scores=raw_scores,
    label="person",
    data={"source": "detector-a"},
    embedding=np.array([0.1, 0.3, 0.6], dtype=float),
)
```

Guidelines:

- Keep one `Detection` per detected object.
- Use consistent point shapes within the same tracker stream.
- Use `label` to keep categories from cross-matching.
- Store appearance features in `embedding` or auxiliary values in `data`.
- If you track a single point, a rank-1 array is promoted to shape `(1, d)`.

## 2) Canonical tracker loop

```python
from norfair.tracker import Detection, Tracker
from norfair.filter import OptimizedKalmanFilterFactory

tracker = Tracker(
    distance_function="euclidean",
    distance_threshold=20,
    hit_counter_max=15,
    initialization_delay=3,
    pointwise_hit_counter_max=4,
    detection_threshold=0.4,
    filter_factory=OptimizedKalmanFilterFactory(),
    past_detections_length=4,
)

for frame_idx, frame_detections in enumerate(detection_stream):
    if frame_detections is None:
        tracked_objects = tracker.update()
    else:
        tracked_objects = tracker.update(
            detections=[Detection(points=pts, label=label) for pts, label in frame_detections],
            period=skip_period,
        )

    # consume tracked_objects here
```

Rules of thumb:

- Call `tracker.update()` on skipped or empty frames so the filter can predict forward.
- On frames where the detector was skipped for multiple frames, pass the same skip count in `period`.
- If you also need a coordinate transform, pass `coord_transformations=` on the same update call.
- For no-detection frames with a coordinate transform, pass `detections=[]` rather than `None`.

## 3) Choose a distance function

### Centroid or point tracking

Use Euclidean-style distances when each object is represented by points in the same order.

```python
tracker = Tracker("euclidean", distance_threshold=15)
# or
tracker = Tracker("mean_euclidean", distance_threshold=8)
# or
tracker = Tracker("frobenius", distance_threshold=12)
```

Good when:

- The detector returns centroids.
- The detector returns keypoints with fixed ordering.
- You want a simple spatial tracker.

### Box tracking

Use `iou` when detections are boxes represented by two corner points or an equivalent flattened `xyxy` layout.

```python
tracker = Tracker("iou", distance_threshold=0.35)
```

Remember that Norfair uses a distance, so lower is better and `1 - IoU` is the actual score being compared.

### Keypoint-heavy tracking

Use the keypoint helpers when some points are missing or low confidence.

```python
from norfair.distances import create_keypoints_voting_distance

tracker = Tracker(
    distance_function=create_keypoints_voting_distance(
        keypoint_distance_threshold=12.0,
        detection_threshold=0.5,
    ),
    distance_threshold=0.5,
)
```

### Normalized distances

Use normalized distances when image size matters.

```python
from norfair.distances import create_normalized_mean_euclidean_distance

tracker = Tracker(
    distance_function=create_normalized_mean_euclidean_distance(height=720, width=1280),
    distance_threshold=0.02,
)
```

### Custom scalar distance

Pass a callable that takes `(detection, tracked_object)` and returns a finite float.

```python
import numpy as np

def appearance_aware_distance(detection, tracked_object):
    spatial = np.linalg.norm(detection.points - tracked_object.estimate)
    if detection.embedding is None or tracked_object.last_detection.embedding is None:
        return spatial
    appearance = np.linalg.norm(detection.embedding - tracked_object.last_detection.embedding)
    return 0.7 * spatial + 0.3 * appearance

tracker = Tracker(
    distance_function=appearance_aware_distance,
    distance_threshold=15.0,
)
```

Notes:

- Custom callables are treated as scalar distances.
- The tracker prints a warning when a scalar callable is used, because vectorized built-ins are faster.
- Return finite values only. `NaN` triggers a hard failure before matching.

## 4) Use labels correctly

Labels are the simplest way to keep classes separated.

```python
person = Detection(points=person_points, label="person")
car = Detection(points=car_points, label="car")
```

Recommendations:

- Use the same label vocabulary for detections and tracked objects.
- Keep labels stable across frames.
- Do not rely on label coercion. Use simple hashable values such as strings or integers.

Behavior to remember:

- A label mismatch blocks a match.
- If some detections have labels and others do not, scalar distances warn about mixed labeled/unlabeled input.
- Vectorized label gating is still strict, so use one label convention per tracker stream.

## 5) Tune lifecycle counters

Lifecycle tuning is often more important than the distance formula.

| Problem | Knob | Direction |
| --- | --- | --- |
| Tracks start too slowly | `initialization_delay` | Lower it |
| Tracks disappear too quickly | `hit_counter_max` | Raise it |
| One-point noise flickers too much | `pointwise_hit_counter_max` | Raise it |
| Low-confidence keypoints keep matching | `detection_threshold` | Raise it |
| Objects get matched when too far apart | `distance_threshold` | Lower it |

Suggested starting point:

```python
tracker = Tracker(
    distance_function="euclidean",
    distance_threshold=20,
    hit_counter_max=15,
    initialization_delay=3,
)
```

How to interpret counters:

- `age` increases once per tracker step.
- `hit_counter` is the main object liveness counter.
- `point_hit_counter` tracks point-level recency.
- `current_min_distance` is a debugging hint, not a decision value.
- `total_object_count` counts initialized objects, not necessarily final unique identities after ReID merges.

## 6) Track with coordinate transforms

If a moving camera is producing relative-frame detections but you want consistent world-space tracking, supply a transformation object with `abs_to_rel` and `rel_to_abs` methods.

```python
tracked_objects = tracker.update(
    detections=detections,
    coord_transformations=coord_transform,
)
```

Rules:

- Detections keep relative points in `points` and transformed points in `absolute_points`.
- Tracked objects estimate in the same relative/absolute dual space.
- `get_estimate(absolute=True)` only works after a transformation has been provided.

## Recover tracks after occlusion with ReID

Use ReID when spatial prediction alone is not enough.

```python
import numpy as np
from norfair.tracker import Tracker

def reid_distance(new_obj, old_obj):
    new_emb = new_obj.last_detection.embedding
    if new_emb is None:
        for det in reversed(new_obj.past_detections):
            if det.embedding is not None:
                new_emb = det.embedding
                break
    old_emb = old_obj.last_detection.embedding
    if old_emb is None:
        for det in reversed(old_obj.past_detections):
            if det.embedding is not None:
                old_emb = det.embedding
                break
    if new_emb is None or old_emb is None:
        return 1.0
    return float(np.linalg.norm(new_emb - old_emb))

tracker = Tracker(
    distance_function="euclidean",
    distance_threshold=20,
    initialization_delay=1,
    past_detections_length=5,
    reid_distance_function=reid_distance,
    reid_distance_threshold=0.2,
    reid_hit_counter_max=30,
)
```

ReID workflow notes:

- Keep `reid_hit_counter_max` set if you want dead tracks to survive long enough for recovery.
- Keep `initialization_delay` positive so a new candidate can become a matched initializing object before the ReID merge step.
- Store appearance cues in `Detection.embedding` or `Detection.data`.
- Use `past_detections_length` so the distance function can recover an older embedding if the latest one is missing.

## 8) Debug without drawing

If you want a quick textual readout, inspect IDs and counters directly.

```python
for obj in tracked_objects:
    print(obj.id, obj.label, obj.age, obj.hit_counter, obj.last_distance)
```

If you need a formatted table, use `print_objects_as_table(tracked_objects)` after the objects have at least one numeric `last_distance`.

## 9) Run the bundled smoke scripts

- `scripts/tracker_smoke.py` checks the basic loop, skipped frames, labels, `validate_points`, `get_cutout`, and the NaN guard.
- `scripts/reid_smoke.py` exercises same-label occlusion and ReID recovery in a tiny synthetic scenario.

## When to route elsewhere

- If you need frame annotation, track drawing, or video output, route to [video-visualization](../../video-visualization/).
- If you need MOTChallenge evaluation or metrics, route to [evaluation](../../evaluation/).
