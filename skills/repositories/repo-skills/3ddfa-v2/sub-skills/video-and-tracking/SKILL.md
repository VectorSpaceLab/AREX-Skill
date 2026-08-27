---
name: "video-and-tracking"
description: "Run 3DDFA_V2 video, smoothing, and manual webcam tracking workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Video and tracking

Use this sub-skill for 3DDFA_V2 video-file processing and smoothing. Webcam
support exists in the source repo but remains a manual, hardware-dependent
workflow.

## When to read

Read this sub-skill when the task asks to:

- Run `demo_video.py` or `demo_video_smooth.py` on an AVI/MP4 file.
- Produce tracked `2d_sparse`, `2d_dense`, or `3d` video outputs.
- Tune `n_pre`, `n_next`, `start`, or `end` frame-window settings.
- Diagnose `imageio`, `ffmpeg`, tracking drift, or webcam/display issues.

## Before running

1. Build and smoke-test the checkout with `../setup-and-assets/`.
2. Confirm `imageio` and `imageio-ffmpeg` are installed.
3. Start with the sample clip if the user's input format is uncertain.

## Basic video wrapper

The basic wrapper preserves the original `demo_video.py` CLI. Put original
arguments after `--`:

```bash
python <skill-root>/sub-skills/video-and-tracking/scripts/run-video.py \
  --repo-root <checkout> -- \
  -f <video-path> -o 3d --onnx
```

## Smoothed video wrapper

The smoothed wrapper preserves the original `demo_video_smooth.py` CLI:

```bash
python <skill-root>/sub-skills/video-and-tracking/scripts/run-video-smooth.py \
  --repo-root <checkout> -- \
  -f <video-path> -o 2d_sparse -n_pre 1 -n_next 1 --onnx
```

## Tracking behavior

- The first frame uses detection; later frames track from the previous landmark
  state.
- If the ROI area becomes too small, the demo re-runs face detection.
- Motion that is too fast or head pose beyond roughly 90 degrees can make the
  lightweight tracker fail.
- Smoothing uses a simple average over `n_pre + n_next + 1` frames and drops or
  pads boundary frames.

## Webcam boundary

The repo has a webcam script that uses `imageio.get_reader("<video0>")` and
`cv2.imshow`. This skill documents the workflow in `references/workflows.md`,
but does not provide an automated webcam wrapper because it needs live camera
hardware, GUI display access, and manual quit handling.

## Troubleshooting

Read `references/troubleshooting.md` for video-specific failure recovery and
`../../references/troubleshooting.md` for shared build/import failures.
