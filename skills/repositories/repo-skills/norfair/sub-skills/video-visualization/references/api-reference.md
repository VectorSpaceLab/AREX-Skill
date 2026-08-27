# Norfair video, drawing, path, and camera-motion API reference

This reference records the verified public contracts needed for visualization workflows. It avoids detector setup and tracker tuning; route those decisions to `../../tracking-core/SKILL.md`.

## Import map

| Symbol | Recommended import | Use |
| --- | --- | --- |
| `Video` | `from norfair import Video` or `from norfair.video import Video` | Open a camera or video file, iterate OpenCV BGR frames, and lazily write an output video. |
| `VideoFromFrames` | `from norfair.video import VideoFromFrames` | Iterate a MOT-style image sequence described by `seqinfo.ini`; optionally write `save_path/videos/<sequence>.mp4`. Not exported from `from norfair import ...` in the inspected package. |
| `draw_points` | `from norfair.drawing import draw_points` | Draw point/keypoint detections or tracked objects. Accepts `Detection` or `TrackedObject` sequences. |
| `draw_boxes` | `from norfair.drawing import draw_boxes` | Draw boxes represented by two 2-D points `[[x0, y0], [x1, y1]]`. Accepts `Detection` or `TrackedObject` sequences. |
| `draw_tracked_objects` | `from norfair.drawing import draw_tracked_objects` | Deprecated wrapper around point drawing for older tracked-object snippets. Prefer `draw_points`. |
| `draw_tracked_boxes` | `from norfair.drawing import draw_tracked_boxes` | Deprecated wrapper around box drawing for older tracked-box snippets. Prefer `draw_boxes`. |
| `Paths` | `from norfair.drawing import Paths` | Draw relative frame-space trajectory trails from tracked object estimates. |
| `AbsolutePaths` | `from norfair.drawing import AbsolutePaths` | Draw trajectory trails in absolute coordinates using a current coordinate transformation. |
| `FixedCamera` | `from norfair.drawing import FixedCamera` | Render a larger stabilized canvas for translation-only camera motion. |
| `draw_absolute_grid` | `from norfair.drawing import draw_absolute_grid` | Overlay a camera-motion debugging grid in absolute coordinates. |
| `Color`, `Palette` | `from norfair.drawing import Color, Palette` | BGR color constants and deterministic palette selection by id/label. |
| `Drawable`, `Drawer` | `from norfair.drawing import Drawable, Drawer` | Internal-friendly wrappers for normalizing `Detection`/`TrackedObject` drawables and OpenCV primitives. |
| `MotionEstimator` | `from norfair.camera_motion import MotionEstimator` | Estimate a coordinate transformation from optical flow between frames. |
| `TranslationTransformationGetter` | `from norfair.camera_motion import TranslationTransformationGetter` | Motion model for pan/tilt-like translations; required for `FixedCamera`. |
| `HomographyTransformationGetter` | `from norfair.camera_motion import HomographyTransformationGetter` | Motion model for homographies such as rotation, zoom, or more general camera motion. |
| `CoordinatesTransformation`, `TransformationGetter`, `TranslationTransformation`, `HomographyTransformation` | `from norfair.camera_motion import ...` | Abstract and concrete coordinate-transform classes implementing `abs_to_rel(points)` and `rel_to_abs(points)`. |

## `Video`

Constructor:

```python
Video(
    camera: int | None = None,
    input_path: str | None = None,
    output_path: str = ".",
    output_fps: float | None = None,
    label: str = "",
    output_fourcc: str | None = None,
    output_extension: str = "mp4",
)
```

Key behavior:

- Set exactly one input source: `camera=<int>` for a camera device or `input_path="file.mp4"` for a video file. Passing neither or both raises `ValueError`.
- `input_path` is expanded for `~`, checked for existence, and rejected if OpenCV reports zero frames.
- Iteration yields OpenCV BGR `numpy.ndarray` frames until `VideoCapture.read()` returns `False` or `None`.
- `write(frame)` lazily creates an OpenCV `VideoWriter` on the first written frame, using that frame's current size. Resize before the first write if output dimensions should differ from input dimensions.
- If `output_path` is a directory, the output path becomes `<input-stem>_out.<output_extension>` inside that directory. If it is a file path, that exact path is used.
- Codec selection defaults to `mp4v` for `.mp4` and `XVID` for `.avi`. For other extensions, pass `output_fourcc` or choose a supported suffix.
- `show(frame, downsample_ratio=1.0)` uses an OpenCV GUI window; avoid it in headless sessions and write video instead.

## `VideoFromFrames`

Constructor:

```python
from norfair.video import VideoFromFrames

frames = VideoFromFrames(input_path, save_path=".", information_file=None, make_video=True)
```

Use it for frame folders that contain a MOT-style `seqinfo.ini`. Required keys include `frameRate`, `imWidth`, `imHeight`, `seqLength`, `imExt`, and `imDir`.

Behavior:

- `for frame in frames:` reads `input_path/<imDir>/<six-digit-frame-number><imExt>` with `cv2.imread`.
- `update(frame)` writes a processed frame to the `VideoWriter` created under `save_path/videos/<sequence>.mp4` when `make_video=True`.
- `cv2.imread` can return `None` for missing/corrupt frames; caller code should validate each frame before drawing.

## Drawing detections and tracks

### `draw_points`

```python
draw_points(
    frame,
    drawables=None,
    radius=None,
    thickness=None,
    color="by_id",
    draw_labels=True,
    text_size=None,
    draw_ids=True,
    draw_points=True,
    text_thickness=None,
    text_color=None,
    hide_dead_points=True,
    draw_scores=False,
)
```

- Modifies `frame` in place and returns the resulting frame.
- `drawables` may be a sequence of `Detection` or `TrackedObject` instances.
- For detections, all points are treated as live. For tracked objects, `hide_dead_points=True` skips points whose corresponding `TrackedObject.live_points` value is `False`; if all points are dead, the object is not drawn.
- Color options are BGR tuples, hex strings such as `"#ff0000"`, `Color` attribute names such as `"red"`, or strategies `"by_id"`, `"by_label"`, and `"random"`.
- Deprecated parameters still exist (`detections`, `label_size`, `color_by_label`) but prefer the modern names above.

### `draw_boxes`

```python
draw_boxes(
    frame,
    drawables=None,
    color="by_id",
    thickness=None,
    draw_labels=False,
    text_size=None,
    draw_ids=True,
    text_color=None,
    text_thickness=None,
    draw_box=True,
    draw_scores=False,
)
```

- Modifies `frame` in place and returns the frame.
- Each drawable must represent a box as two points: top-left and bottom-right corners.
- Use `draw_box=False` for labels/ids without a rectangle.
- Deprecated aliases and parameters (`draw_tracked_boxes`, `random_color`, `line_color`, `line_width`, `label_size`) route to this modern function.

## Color and low-level drawing

- `Color` constants are OpenCV BGR tuples, not RGB. Example: `Color.red` is the BGR tuple for red as OpenCV expects it.
- `Palette.set("tab10" | "tab20" | "colorblind")` selects a built-in palette. `Palette.set([Color.red, "#00ff00", (255, 0, 0)])` accepts custom colors.
- `Palette.set_default_color(color)` controls the fallback used when a drawable lacks an id or label for `"by_id"` / `"by_label"` selection.
- `Drawable(obj)` normalizes `Detection` and `TrackedObject` data into `.points`, `.id`, `.label`, `.scores`, and `.live_points` for the drawing functions.
- `Drawer` wraps OpenCV primitives: `circle`, `rectangle`, `line`, `text`, `cross`, and `alpha_blend`. Use it only when the higher-level draw helpers are too coarse.

## Paths and absolute paths

`Paths` constructor:

```python
Paths(get_points_to_draw=None, thickness=None, color=None, radius=None, attenuation=0.01)
```

- `draw(frame, tracked_objects)` returns a blended frame; unlike most drawers, it is not purely in-place.
- It records trails in relative frame coordinates. Do not use it as the main path drawer when tracker objects have camera-motion coordinate transformations; use `AbsolutePaths` instead.
- `attenuation=0` keeps the trail forever; larger values fade old path pixels faster.

`AbsolutePaths` constructor:

```python
AbsolutePaths(get_points_to_draw=None, thickness=None, color=None, radius=None, max_history=20)
```

- `draw(frame, tracked_objects, coord_transform=coord_transform)` returns the frame with absolute-coordinate history rendered into the current relative frame.
- Requires tracked objects that can return absolute estimates (`obj.get_estimate(absolute=True)`) and a non-`None` coordinate transform for moving-camera path rendering.
- It is intentionally slower: drawing cost grows with `max_history * number_of_tracked_objects`.

## Camera motion and coordinate transformations

`MotionEstimator` constructor:

```python
MotionEstimator(
    max_points=200,
    min_distance=15,
    block_size=3,
    transformations_getter=None,
    draw_flow=False,
    flow_color=None,
    quality_level=0.01,
)
```

`update(frame, mask=None)` behavior:

- Converts the BGR frame to grayscale, samples strong corners, computes sparse optical flow, and asks the selected `TransformationGetter` to produce a coordinate transformation.
- Returns a `CoordinatesTransformation` instance or `None` when estimation fails. On the first frame, treat `None` as no motion yet and use an identity/fallback transform if downstream drawing requires one.
- `mask` is a single-channel array shaped like the frame height/width; nonzero areas are eligible for corner sampling. Build it before drawing overlays so text/boxes do not become optical-flow features.
- `draw_flow=True` draws optical-flow lines/circles on the provided frame for inspection.

Transformation getters:

- `TranslationTransformationGetter(bin_size=0.2, proportion_points_used_threshold=0.9)` estimates the modal optical-flow vector and returns `TranslationTransformation(movement_vector)`.
- `HomographyTransformationGetter(method=None, ransac_reproj_threshold=3, max_iters=2000, confidence=0.995, proportion_points_used_threshold=0.9)` calls OpenCV homography estimation and returns `HomographyTransformation(homography_matrix)` when enough points exist.
- Both getters return `(update_reference_frame: bool, transformation)`. `MotionEstimator` uses this internally to decide whether to reset the reference frame.

Coordinate transformations:

- `CoordinatesTransformation` defines `abs_to_rel(points)` and `rel_to_abs(points)`.
- `TranslationTransformation(movement_vector)` maps absolute to relative with `points + movement_vector`, and relative to absolute with `points - movement_vector`.
- `HomographyTransformation(homography_matrix)` applies a projective transform for `abs_to_rel` and the inverse matrix for `rel_to_abs`.

## Stabilization and absolute grid

`FixedCamera(scale=2, attenuation=0.05)`:

- `adjust_frame(frame, coord_transformation)` renders the current frame on a larger, fading background.
- Only use it with `TranslationTransformation`; homographies are explicitly not supported by this renderer.
- Apply it after all other draw calls. Drawing on the enlarged stabilized canvas with ordinary frame-relative coordinates will be wrong.

`draw_absolute_grid(frame, coord_transformations, grid_size=20, radius=2, thickness=1, color=Color.black, polar=False)`:

- Draws visible grid points after transforming absolute grid coordinates to the current frame with `coord_transformations.abs_to_rel(...)`.
- Passing `coord_transformations=None` draws the initial untransformed grid, useful on the first frame or when estimation failed.
- Use `polar=True` only when the spherical-grid perspective should appear pole-oriented; default `False` is the usual equator-like view.
