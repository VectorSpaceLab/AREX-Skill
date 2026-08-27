# Media utilities troubleshooting

Use this reference when image/video/drawing/geometry/assets code imports but
behaves unexpectedly. For API groups, read [media reference](media-reference.md);
for OpenCV-specific decisions, read [backend compatibility](backend-compatibility.md).

## OpenCV warning during import

**Symptom**

Importing `supervision` prints a warning that `opencv-python` is not installed
and the fallback backend is active.

**Fix**

This is not an error for Supervision-owned APIs. Keep the fallback when the task
only needs package drawing/image/video helpers. Install exactly one OpenCV wheel
only when the user needs native OpenCV behavior, GUI windows, webcam capture, or
compatibility with an external OpenCV pipeline.

Diagnostic:

```bash
python -c "from supervision import _cv2; print(_cv2.BACKEND_NAME)"
```

Restart Python after changing OpenCV packages because backend selection happens
at import time.

## Image URL or cache failures

**Symptoms**

- `load_image_from_url(...)` times out or returns decode errors.
- A cached URL keeps returning an old image.
- Network access is not allowed.

**Fix**

- Check whether the task can use a local image or synthetic fixture instead of a
  network URL.
- Set `timeout` explicitly for slow links.
- Use `force_reload=True` when stale cache content is suspected.
- Use `use_cache=False` when reproducibility matters more than repeated-download
  speed.
- Do not require URL downloads in generated or verification workflows unless the
  user explicitly accepts network access.

## BGR/RGB color confusion

**Symptoms**

- Colors look swapped after Pillow/OpenCV conversion.
- Drawn colors are red/blue reversed.

**Fix**

- NumPy scenes in Supervision are OpenCV-style BGR.
- PIL images are RGB.
- Use `sv.cv2_to_pillow(image)` and `sv.pillow_to_cv2(image)` at boundaries.
- Use `sv.Color(...).as_bgr()` when passing raw color tuples to lower-level
  NumPy/OpenCV-style functions.
- High-level annotators accept `sv.Color` and handle conversion internally.

## Video decode/write problems

**Symptoms**

- `get_video_frames_generator` yields no frames.
- `VideoSink` writes a file that cannot be opened.
- Output video has wrong resolution or frame rate.
- `process_video` fails while preserving audio.

**Fix**

1. Confirm the path is a local readable file. Supervision video helpers are not
   webcam capture APIs.
2. Inspect metadata with `sv.VideoInfo.from_video_path(path)`.
3. Make every `VideoSink.write_frame(...)` frame match `video_info.width` and
   `video_info.height`.
4. Try `process_video(..., preserve_audio=False)` first. Audio preservation adds
   codec/container constraints.
5. If a codec is unsupported in the fallback/PyAV lane, choose a common output
   codec such as `mp4v` or install a compatible native OpenCV/codec stack.
6. Keep model inference and downloads outside the video I/O diagnosis until raw
   decode/write is proven.

## `ImageWindow` or interactive helper fails

**Symptoms**

- Window never opens.
- Mouse or keyboard callbacks do nothing.
- The bundled `draw_zones.py` helper exits with a display/backend error.

**Fix**

- Confirm a desktop/display-capable session exists.
- Avoid GUI helpers in headless containers unless a virtual display is provided.
- Use `opencv-python` rather than `opencv-python-headless` when native OpenCV GUI
  windows are required.
- For non-interactive workflows, save images with `ImageSink` or video with
  `VideoSink` instead of opening a window.

## `draw_image` or overlay placement is wrong

**Symptoms**

- Overlay appears at the wrong location.
- Opacity has no visible effect.
- Overlay spills outside the scene.

**Fix**

- Use `sv.Rect(x, y, width, height)` and verify all values are in the scene
  coordinate system.
- Make the overlay image type/channel count compatible with the scene.
- Keep `opacity` in the expected range for the function call.
- If coordinates come from detections, route the detection-box reasoning to
  [detection-and-zones](../../detection-and-zones/SKILL.md).

## Asset download failures

**Symptoms**

- `download_assets(...)` cannot reach a remote host.
- Checksum validation fails.
- The task cannot use network downloads.

**Fix**

- Import assets with `from supervision.assets import ImageAssets, VideoAssets, download_assets`.
- Treat downloads as optional convenience, not a required runtime dependency.
- Retry only when network access is permitted.
- If checksum validation fails, delete the corrupted downloaded file and retry.
- For tests or deterministic examples, synthesize a tiny local image/video
  fixture instead of downloading public sample media.

## `list_files_with_extensions` finds too much or too little

**Symptoms**

- A batch operation ignores files with uppercase suffixes.
- Recursive search includes unwanted directories.

**Fix**

- Normalize extensions before calling when matching policy matters.
- Decide whether recursion is needed before running a batch operation.
- Filter discovered paths for user-owned input directories; do not run broad
  recursive media operations over arbitrary cache/build directories.

## Geometry anchor confusion

**Symptoms**

- Text/labels appear in a surprising location.
- Polygon center or zone anchor logic seems off.

**Fix**

- `Point`, `Rect`, and `Position` are pixel-coordinate helpers.
- For detection anchors, use `detections.get_anchors_coordinates(...)` from the
  detection sub-skill; it accounts for masks/OBB data when relevant.
- `get_polygon_center` is a general geometry helper; it does not imply object
  occupancy. Use `PolygonZone.trigger(...)` for zone membership.

## Notebook plotting side effects

**Symptoms**

- Plotting code opens large figures or slows batch jobs.
- Display output is not available in a terminal.

**Fix**

Use `plot_image` and `plot_images_grid` in notebook/exploration contexts. In
scripts, write images/videos to files or return arrays for the caller to manage.
Do not add notebook plotting to production-style loops unless the user asked for
interactive exploration.
