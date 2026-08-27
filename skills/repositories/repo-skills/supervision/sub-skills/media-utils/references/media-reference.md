# Media utilities reference

This reference covers `supervision` media, primitive drawing, geometry, file,
notebook, conversion, and asset helpers in version `0.31.0.dev0`. Use
[backend compatibility](backend-compatibility.md) for OpenCV/fallback behavior
and [troubleshooting](troubleshooting.md) for failures.

## Installation and imports

Base utilities are available from the normal package install:

```bash
pip install supervision
```

Prefer public top-level imports when they are exported:

```python
import supervision as sv

image = sv.resize_image(image, resolution_wh=(640, 480))
info = sv.VideoInfo.from_video_path(video_path)
```

Assets helpers are imported from the assets module, not as `sv.assets`:

```python
from supervision.assets import ImageAssets, VideoAssets, download_assets
```

## Image helpers

| API | Purpose | Notes |
| --- | --- | --- |
| `load_image_from_url(value, cv_imread_flags=1, timeout=30.0, use_cache=True, cache_dir=None, force_reload=False)` | Download/decode an image URL into a NumPy array. | Uses a cache when enabled. Network failures and invalid image bytes should be handled by the caller. |
| `crop_image(image, xyxy)` | Crop an image by `xyxy` coordinates. | Coordinates are clipped to image bounds. |
| `scale_image(image, scale_factor)` | Resize by scale factor. | Preserves image type where supported. |
| `resize_image(image, resolution_wh)` | Resize to explicit `(width, height)`. | Use `(width, height)`, not `(height, width)`. |
| `letterbox_image(image, resolution_wh, color=...)` | Resize with padding to fit target resolution. | Useful before model inference when aspect ratio must be preserved. |
| `overlay_image(scene, overlay, opacity, rect)` | Alpha-blend one image into a rectangle on another. | `rect` is a `sv.Rect`; color order follows the scene type. |
| `tint_image(image, color, opacity)` | Overlay a color tint. | `Color` is RGB internally but `.as_bgr()` exists for NumPy/OpenCV scenes. |
| `grayscale_image(image)` | Convert to grayscale. | Output shape/type follows helper behavior. |
| `get_image_resolution_wh(image)` | Return `(width, height)`. | Use this instead of manually reversing shape axes. |
| `ImageSink(target_dir_path, overwrite=False, image_name_pattern="image_{:05d}.png")` | Context manager that writes sequential images. | It creates the target directory and writes one file per appended image. |

## Video helpers

| API | Purpose | Notes |
| --- | --- | --- |
| `VideoInfo(width, height, fps, total_frames=None)` | Container for video metadata. | Use `VideoInfo.from_video_path(...)` for local files. |
| `get_video_frames_generator(source_path, stride=1, start=0, end=None, iterative_seek=False, prefetch=0)` | Yield frames from a local video file. | `source_path` is a file path; webcam capture is application-owned. |
| `VideoSink(target_path, video_info, codec="mp4v")` | Context manager for writing video frames. | Frame shape/resolution must match `video_info`. |
| `process_video(source_path, target_path, callback, max_frames=None, prefetch=32, writer_buffer=32, show_progress=False, progress_message="Processing video", preserve_audio=False)` | Read, transform, and write a video with a callback. | Callback signature is `(frame, index) -> frame`. Avoid long-running model downloads inside it. |
| `FPSMonitor` | Track throughput for loops. | Read the `.fps` property after ticking/updating. |

Example processing skeleton:

```python
import supervision as sv

box_annotator = sv.BoxAnnotator()


def callback(frame, index):
    detections = predict_as_detections(frame)
    return box_annotator.annotate(scene=frame.copy(), detections=detections)

sv.process_video(
    source_path="input.mp4",
    target_path="output.mp4",
    callback=callback,
    show_progress=True,
)
```

Use [annotators](../../annotators/SKILL.md) for the detection visualization
choices inside the callback.

## Primitive drawing and color

These functions draw directly onto NumPy scenes and are lower-level than
annotator classes.

| API | Purpose |
| --- | --- |
| `draw_line`, `draw_rectangle`, `draw_filled_rectangle`, `draw_polygon`, `draw_filled_polygon` | Draw geometric primitives. |
| `draw_text` | Draw text with optional background. |
| `draw_image` | Draw another image into a `Rect` with opacity. |
| `calculate_optimal_text_scale`, `calculate_optimal_line_thickness` | Resolution-aware defaults. |
| `Color(r, g, b, a=255)` | Immutable color object with named constants such as `Color.WHITE`. |
| `ColorPalette(colors)` and `ColorPalette.DEFAULT` | Reusable color sequences with `by_idx(...)`. |

Color gotcha: `Color` stores RGB values conceptually, while NumPy/OpenCV scenes
usually use BGR. Use `color.as_bgr()` when a lower-level API expects BGR tuples.
High-level annotators handle their own color conversion.

## Geometry helpers

| API | Purpose |
| --- | --- |
| `Point(x, y)` | Integer-like point used by `LineZone`, draw anchors, text anchors, and `Rect`. |
| `Rect(x, y, width, height)` | Rectangle used by overlay and crop-style operations. |
| `Position` | Anchor enum shared by detections, labels, and zones. |
| `get_polygon_center(polygon)` | Return a `Point` at a polygon center. |
| `Vector` | Internal/support geometry; use only when a task asks for vector arithmetic. |

When a geometry question is detection-specific, such as box conversion, mask
polygons, OBB corners, NMS, or zones, use
[detection-and-zones](../../detection-and-zones/SKILL.md).

## Conversion helpers

| API | Use |
| --- | --- |
| `cv2_to_pillow(image)` | Convert a BGR NumPy image to a PIL image. |
| `pillow_to_cv2(image)` | Convert a PIL image to a BGR NumPy image. |
| `images_to_cv2(images)` | Normalize a list of image-like inputs to NumPy/OpenCV arrays. |

Most public annotators accept NumPy images and many accept PIL images. Convert
explicitly when downstream code has a strict channel-order assumption.

## File, notebook, and window helpers

| API | Use |
| --- | --- |
| `list_files_with_extensions(directory, extensions, recursive=False)` | Discover files for batch processing. |
| `plot_image`, `plot_images_grid` | Notebook/display utilities for one or more images. |
| `ImageWindow` | Local GUI image display with keyboard/mouse callbacks. |

`ImageWindow` is not a headless-server primitive. Use it only when the user has
a GUI display and wants interaction. For batch scripts, prefer file outputs or
notebook plotting.

## Sample assets

`supervision.assets` provides public sample image/video names and a downloader:

```python
from supervision.assets import ImageAssets, VideoAssets, download_assets

image_path = download_assets(ImageAssets.SOCCER)
video_path = download_assets(VideoAssets.VEHICLES)
```

The downloader performs network access and checksum validation. For generated
or CI-like workflows, avoid requiring asset downloads unless the user explicitly
accepts network use. If a task only needs a tiny fixture, synthesize an image or
video locally instead.
