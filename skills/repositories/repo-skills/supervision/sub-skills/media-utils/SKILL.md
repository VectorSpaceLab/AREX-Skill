---
name: media-utils
description: "Use supervision image, video, drawing, geometry, assets, and
  OpenCV-backend utility APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Media Utils

Use this sub-skill when a task asks for `supervision` image/video/file helpers,
primitive drawing, geometry objects, notebook display helpers, sample assets, or
OpenCV/fallback backend diagnosis.

## Route here for

- Image helpers: `load_image_from_url`, `crop_image`, `resize_image`,
  `letterbox_image`, `overlay_image`, `tint_image`, `grayscale_image`,
  `get_image_resolution_wh`, and `ImageSink`.
- Video helpers: `VideoInfo`, `VideoSink`, `FPSMonitor`,
  `get_video_frames_generator`, and `process_video`.
- Primitive drawing and colors: `draw_text`, `draw_rectangle`, `draw_polygon`,
  `draw_image`, `calculate_optimal_text_scale`, `Color`, and `ColorPalette`.
- Geometry and conversion helpers: `Point`, `Rect`, `Position`,
  `get_polygon_center`, `cv2_to_pillow`, `pillow_to_cv2`, and `images_to_cv2`.
- File, notebook, and assets utilities: `list_files_with_extensions`,
  `plot_image`, `plot_images_grid`, `ImageWindow`, `download_assets`,
  `ImageAssets`, and `VideoAssets`.
- OpenCV dependency migration, fallback backend warnings, video codec issues,
  GUI/window failures, URL/image cache behavior, and asset download problems.

## Route away

- High-level detection/mask/keypoint annotators that take `scene` plus
  `Detections` or `KeyPoints`: use [annotators](../annotators/SKILL.md).
- `Detections`, model adapters, detection masks, detection zones, slicers,
  sinks, and detection utility functions: use
  [detection-and-zones](../detection-and-zones/SKILL.md).
- Dataset layouts, annotation format conversion, and dataset iteration: use
  [datasets](../datasets/SKILL.md).
- Keypoint containers, tracking IDs, `ByteTrack`, and tracker-dependent line
  counting: use [tracking-keypoints](../tracking-keypoints/SKILL.md).
- Evaluation metrics and benchmarking result interpretation: use
  [metrics](../metrics/SKILL.md).

## Start with these references

- [Media reference](references/media-reference.md) for API groups, signatures,
  import paths, and common inputs/outputs.
- [Backend compatibility](references/backend-compatibility.md) for the OpenCV
  optional-backend model, fallback diagnostics, GUI notes, and webcam ownership.
- [Troubleshooting](references/troubleshooting.md) for image URLs/cache, video
  codecs, file formats, color order, assets, and window/display failures.
- Run or read the root [check_supervision_install.py](../../scripts/check_supervision_install.py)
  helper when the task starts with an unknown environment.

## Operating checklist

1. Identify whether the user wants low-level media primitives or high-level
   detection annotation. Route high-level visualization to `annotators`.
2. Confirm the image type and color convention. NumPy images are OpenCV-style
   BGR arrays; PIL images are RGB and should be converted deliberately when
   crossing between APIs.
3. For video, require a local file path. `supervision` does not own webcam
   capture; applications should acquire live frames themselves and pass arrays
   into Supervision annotators or processors.
4. For backend questions, remember that native OpenCV is optional. A standard
   Supervision install can select the documented fallback backend, while a
   compatible already-installed `cv2` is used at import time.
5. For asset helpers, do not assume network access. `download_assets(...)`
   downloads public sample media and verifies checksums, but generated runtime
   guidance should remain useful when downloads are unavailable.
6. Keep answers self-contained. Do not tell future agents to open or run the
   original repository docs, examples, tests, notebooks, scripts, or local
   checkout files as part of runtime operation.

## Common quick checks

```bash
python -c "import supervision as sv; print(sv.__version__)"
python -c "from supervision import _cv2; print(_cv2.BACKEND_NAME)"
python scripts/check_supervision_install.py --json  # run from the root of this generated skill
```

Use the private `_cv2` import only as an installation diagnostic. Application
code should use public `supervision` media, drawing, and annotation APIs.
