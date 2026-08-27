# API Reference

Verified against Norfair 2.3.0 and the bundled source/test evidence for the tracking core.

## Import surface

Prefer the public package surface when possible:

```python
from norfair import Detection, Tracker, FilterPyKalmanFilterFactory, NoFilterFactory, OptimizedKalmanFilterFactory
from norfair.distances import (
    frobenius,
    mean_euclidean,
    mean_manhattan,
    iou,
    get_distance_by_name,
    create_keypoints_voting_distance,
    create_normalized_mean_euclidean_distance,
)
from norfair.utils import validate_points, get_cutout, print_objects_as_table
```

If you only need core tracking and want to avoid optional video or drawing features in a minimal environment, direct imports from `norfair.tracker`, `norfair.filter`, `norfair.distances`, and `norfair.utils` are equivalent for the APIs covered here.

## `Detection`

### Signature

```python
Detection(points: np.ndarray, scores: np.ndarray = None, data: Any = None, label: Hashable = None, embedding=None)
```

### Behavior

- `points` is normalized through `validate_points(...)`.
- Rank-1 input becomes a single point with shape `(1, d)`.
- Rank greater than 2 raises `ValueError`.
- The class stores both `points` and `absolute_points`.
- `absolute_points` starts as a copy of `points` and is updated only when coordinate transformations are provided.
- `scores` is optional. When present, it should be a 1-D array with one score per point.
- `data` is arbitrary user payload.
- `label` is used by the tracker as a matching gate.
- `embedding` is stored for ReID-style workflows and custom distance logic.
- `age` is managed by the tracker.

### Important constraint

Pass NumPy arrays, not plain Python lists, when constructing `Detection`. The constructor expects array-like objects with a `.shape` attribute.

## `validate_points`

```python
validate_points(points: np.ndarray) -> np.ndarray
```

- Rank-1 input is promoted to `(1, d)`.
- Rank > 2 raises a `ValueError` with a shape-focused message.
- The helper does not enforce `d == 2` at runtime, but the tracker and distances are documented around 2D/3D point sets.

## `Tracker`

### Signature

```python
Tracker(
    distance_function,
    distance_threshold,
    hit_counter_max=15,
    initialization_delay=None,
    pointwise_hit_counter_max=4,
    detection_threshold=0,
    filter_factory=OptimizedKalmanFilterFactory(),
    past_detections_length=4,
    reid_distance_function=None,
    reid_distance_threshold=0,
    reid_hit_counter_max=None,
)
```

### Constructor parameters

| Parameter | Meaning |
| --- | --- |
| `distance_function` | String name or custom scalar callable. String names are resolved with `get_distance_by_name(...)`. Custom callables are wrapped as scalar distances. |
| `distance_threshold` | Maximum allowed match distance. Matching uses a strict `<` comparison. |
| `hit_counter_max` | Upper cap for the tracker hit counter. Also governs how long an unmatched object can survive without ReID. |
| `initialization_delay` | How many hit-counter points are required before an object becomes initialized and is returned. Default is `int(hit_counter_max / 2)`. Must be `0 <= initialization_delay < hit_counter_max`. |
| `pointwise_hit_counter_max` | Upper cap for per-point liveness. The effective cap is at least `period`. |
| `detection_threshold` | Per-point score threshold below which points are ignored during update. |
| `filter_factory` | Factory used to create the per-object predictive filter. |
| `past_detections_length` | Number of past detections to retain per object. Must be non-negative. |
| `reid_distance_function` | Optional scalar callable used to merge initialized-but-unmatched candidates with dead/unmatched objects. Wrapped in `ScalarDistance`. |
| `reid_distance_threshold` | Maximum ReID distance. Matching uses strict `<`. |
| `reid_hit_counter_max` | Optional lifespan for dead objects kept around for ReID recovery. |

### Lifecycle rules

- New objects start with `hit_counter = period`.
- `hit_counter` increases by `2 * period` on a match and is capped at `hit_counter_max`.
- `hit_counter` decreases by `1` on each tracker step when unmatched.
- Objects are returned only when they are initialized and `hit_counter >= 0`.
- With `reid_hit_counter_max=None`, stale objects are dropped immediately once they are no longer alive.
- With ReID enabled, dead objects may remain until their ReID counter expires.
- `initialization_delay=0` makes objects visible immediately, but they may appear and disappear quickly if the detector is unstable.

### Methods and properties

#### `update`

```python
update(detections: Optional[List[Detection]] = None, period: int = 1, coord_transformations: Optional[CoordinatesTransformation] = None) -> List[TrackedObject]
```

- Feeds one frame into the tracker.
- `detections` may be omitted or `None` when no detections are available, but if `coord_transformations` is provided, pass an empty list instead of `None` so the coordinate update loop has something to iterate over.
- `period` should match the detector skip interval on frames where detections were produced after skipping frames.
- `coord_transformations` updates both detections and tracked objects in the absolute/relative coordinate pipeline.
- Returns the list of currently active tracked objects.

#### `get_active_objects()`

Returns initialized objects whose `hit_counter` is non-negative.

#### `current_object_count`

Number of active objects returned by `get_active_objects()`.

#### `total_object_count`

Number of objects ever initialized by this tracker factory. ReID merges can still leave this count larger than the number of final surviving identities.

## `TrackedObject`

Tracked objects are created by `Tracker`; users should not instantiate them manually.

### Notable attributes and properties

| Name | Meaning |
| --- | --- |
| `estimate` | Current estimated position, in relative coordinates unless a coordinate transformation is active. |
| `estimate_velocity` | Kalman velocity estimate. |
| `id` | Tracker-local ID, assigned after initialization completes. |
| `global_id` | Globally unique ID from the factory. |
| `initializing_id` | Temporary internal ID used while the object is still initializing. |
| `label` | Inherited from the last matched detection. |
| `last_detection` | Most recent matched detection. Useful for embeddings and diagnostics. |
| `last_distance` | Distance from the most recent successful match. |
| `current_min_distance` | Debugging aid populated from the current distance matrix. |
| `age` | Number of tracker steps the object has survived. |
| `hit_counter` | Main liveness counter. |
| `reid_hit_counter` | ReID-specific liveness counter, if enabled. |
| `live_points` | Boolean mask of per-point liveness. |
| `past_detections` | Retained past detections, sampled over the object's lifetime. |
| `is_initializing` | True until the hit counter crosses `initialization_delay`. |

### Methods

- `get_estimate(absolute=False)` returns relative coordinates by default; pass `absolute=True` only when a coordinate transformation was supplied.
- `hit(...)`, `merge(...)`, and `tracker_step()` are internal control methods and are not intended for user code.

## Distance helpers

### Built-in names

`get_distance_by_name(name)` accepts:

- Scalar: `frobenius`, `mean_euclidean`, `mean_manhattan`
- Vectorized: `iou`, `iou_opt` (deprecated alias for `iou`)
- SciPy metrics: `braycurtis`, `canberra`, `chebyshev`, `cityblock`, `correlation`, `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`, `kulczynski1`, `mahalanobis`, `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`, `sokalmichener`, `sokalsneath`, `sqeuclidean`, `yule`

### Distance semantics

- Lower is better.
- Matching uses strict `< distance_threshold`.
- Custom scalar callables are wrapped and compared pairwise.
- Custom callables should return finite floats.
- If a distance function returns `NaN`, the tracker raises a `ValueError` before matching.

### `frobenius`

Frobenius norm between detection points and tracked-object estimate.

### `mean_euclidean`

Mean Euclidean distance across points.

### `mean_manhattan`

Mean Manhattan distance across points.

### `iou`

Vectorized IoU distance for boxes in `[x_min, y_min, x_max, y_max]` form after flattening. The tracker typically feeds this with two-point box detections whose flattened coordinates become `xyxy`.

### `create_keypoints_voting_distance(keypoint_distance_threshold, detection_threshold)`

Returns a scalar callable that votes by point-wise proximity and scores.

### `create_normalized_mean_euclidean_distance(height, width)`

Returns a scalar callable that normalizes coordinate differences by image size before averaging Euclidean distance.

## Filter factories

### `FilterPyKalmanFilterFactory`

```python
FilterPyKalmanFilterFactory(R=4.0, Q=0.1, P=10.0)
```

- Wraps `filterpy.KalmanFilter`.
- Useful when you want explicit Kalman matrix tuning or a custom filterpy-compatible subclass.
- `R` controls measurement noise, `Q` process noise, `P` initial covariance on position variables.

### `OptimizedKalmanFilterFactory`

```python
OptimizedKalmanFilterFactory(R=4.0, Q=0.1, pos_variance=10, pos_vel_covariance=0, vel_variance=1)
```

- Faster internal tracker filter.
- Good default for ordinary tracking.

### `NoFilterFactory`

```python
NoFilterFactory()
```

- No predictive velocity model.
- Best treated as a comparison or debugging aid, not the default production choice.

## Utility helpers

### `get_cutout(points, image)`

Returns a rectangular crop using the min/max x/y from the point set.

- No bounds clipping is performed.
- If points are outside the image, the crop may be empty or truncated by NumPy slicing.
- Useful for extracting appearance embeddings from a detection crop.

### `print_objects_as_table(tracked_objects)`

Prints a debugging table with object id, age, hit counter, last distance, and initializing id.

- Call it only when `last_distance` is already numeric for every object you pass in.
- For brand-new objects, `last_distance` may still be `None`.

## Coordinate transformation contract

When `coord_transformations` is supplied:

- Each `Detection` updates its `absolute_points`.
- Each `TrackedObject` stores an `abs_to_rel` callable.
- `TrackedObject.get_estimate(absolute=False)` returns relative coordinates.
- `TrackedObject.get_estimate(absolute=True)` returns absolute coordinates.

The tracker expects a transformation object with `abs_to_rel(...)` and `rel_to_abs(...)` methods.
