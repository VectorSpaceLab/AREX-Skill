# CLI Reference

This sub-skill covers the `demo_superglue.py` command line.

## Core options

| Flag | Default | Meaning | Notes |
| --- | --- | --- | --- |
| `--input` | `0` | Input source for live matching | Accepts a USB webcam id, an IP/RTSP URL, an image directory, or a video file. Digits are treated as webcam ids; `http`/`rtsp` sources are treated as IP cameras. |
| `--output_dir` | `None` | Directory for rendered output frames | When set, the demo writes one image per processed pair. |
| `--image_glob` | `*.png *.jpg *.jpeg` | Directory glob patterns | Used only when `--input` is a directory. Multiple patterns are allowed. |
| `--skip` | `1` | Frame skip factor | Applies to image directories and video files. |
| `--max_length` | `1000000` | Maximum number of processed frames | Useful for bounded sequence runs and smoke tests. |
| `--resize` | `640 480` | Resize before inference | Two values resize to an exact width/height. One positive value resizes the larger dimension to that value. `-1` disables resize. |
| `--superglue` | `indoor` | SuperGlue weight set | `indoor` is the default. Use `outdoor` for outdoor scenes. |
| `--max_keypoints` | `-1` | SuperPoint keypoint cap | `-1` keeps all detected keypoints. |
| `--keypoint_threshold` | `0.005` | SuperPoint detector threshold | Lower values detect more keypoints. |
| `--nms_radius` | `4` | SuperPoint non-maximum suppression radius | Smaller values keep denser detections. |
| `--sinkhorn_iterations` | `20` | SuperGlue Sinkhorn iterations | Higher values cost more time. |
| `--match_threshold` | `0.2` | SuperGlue match threshold | Lower values accept more matches. |
| `--show_keypoints` | `False` | Draw detected keypoints in the visualization | Helpful when debugging sparse detections. |
| `--no_display` | `False` | Disable the OpenCV GUI window | Use this on headless or remote servers. |
| `--force_cpu` | `False` | Force CPU execution | Overrides automatic CUDA use. |

## Input handling notes

- Directory mode collects the configured glob patterns, sorts the matches, applies `--skip`, and then truncates to `--max_length`.
- Video-file mode uses OpenCV frame indexing and the same skip and length controls.
- USB webcam and IP/RTSP sources stream frames live.
- IP/RTSP sources are handled with a background reader thread; if the camera stops responding, the stream ends.

## Output conventions

- The demo writes images as `matches_%06_%06.png` when `--output_dir` is set.
- The first number is the anchor-frame index and the second number is the live-frame index.
- The visualization uses confidence-colored match lines and optional keypoints.
- The displayed text reports the current keypoint threshold, match threshold, and frame indices.

## Practical defaults

- Indoor scenes usually work with the default settings.
- Outdoor or large-field-of-view scenes often need a larger resize and more keypoints.
- For interactive use, keep the OpenCV window focused so keyboard controls reach the demo.