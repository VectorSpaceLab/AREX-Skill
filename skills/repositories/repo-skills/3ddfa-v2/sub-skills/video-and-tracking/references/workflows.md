# Video and tracking workflows

## Video file workflow

```bash
python <skill-root>/sub-skills/video-and-tracking/scripts/run-video.py \
  --repo-root <checkout> -- \
  -f <video-path> -o 3d --onnx
```

The result is written as an MP4 under `examples/results/videos/`.

## Smoothed video workflow

```bash
python <skill-root>/sub-skills/video-and-tracking/scripts/run-video-smooth.py \
  --repo-root <checkout> -- \
  -f <video-path> -o 2d_sparse -n_pre 1 -n_next 1 --onnx
```

Useful options:

- `-n_pre` / `-n_next`: smoothing window around the current frame.
- `-s` / `-e`: start and end frame limits.
- `--onnx`: use the CPU-friendly ONNX path.

## Webcam note

The source repo's webcam script reads from `imageio.get_reader("<video0>")` and
shows a live `cv2.imshow` window. Keep it as a manual-only workflow because it
requires camera permissions, display access, and interactive quit handling.

## Tracking behavior

- The first frame uses detection, then later frames reuse the previous face
  shape as a tracker seed.
- When the tracked ROI becomes too small, the script falls back to face
  detection.
- Rapid motion and extreme pose can break the lightweight tracker.
- The smoothing helper pads the beginning and loses the last `n_next` frames by
  design.
