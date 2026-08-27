---
name: video-visualization
description: "Guide Norfair video I/O, overlay drawing, path rendering, and
  camera-motion stabilization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# video-visualization

Use this sub-skill when the task is about Norfair's OpenCV-backed video and visualization utilities: reading video files or camera feeds with `Video`, iterating frame sequences with `VideoFromFrames`, writing annotated video, drawing detections or tracked objects as points/boxes, keeping trajectories visible, estimating moving-camera transforms, rendering absolute paths/grids, or stabilizing a panning/tilting camera with `FixedCamera`.

## Route here when

- Opening an input video, camera device, or MOT-style frame folder and writing an annotated output video.
- Choosing between `draw_points`, `draw_boxes`, legacy `draw_tracked_objects`, and legacy `draw_tracked_boxes` for centroids, keypoints, or two-corner boxes.
- Rendering relative trails with `Paths` or motion-aware trails with `AbsolutePaths`.
- Estimating camera motion with `MotionEstimator`, `TranslationTransformationGetter`, or `HomographyTransformationGetter` and passing coordinate transformations to downstream overlays.
- Debugging moving-camera behavior with `FixedCamera` or `draw_absolute_grid`.
- Customizing visual colors with `Color`, `Palette`, `Drawable`, or `Drawer`.

## What this covers

- OpenCV frame iteration and output writing for file, camera, and frame-sequence workflows.
- Point and box drawing plus the color/palette system.
- Relative and absolute path rendering for tracked-object histories.
- Motion estimation for translation and homography camera movement.
- Fixed-camera stabilization and absolute-grid debugging.

## Typical workflow

1. Open [API reference](references/api-reference.md) to confirm import paths, accepted drawable shapes, return values, and which classes are top-level exports versus module-level imports.
2. Pick the closest loop from [workflows](references/workflows.md): video round-trip, points-vs-boxes overlay, path rendering, `VideoFromFrames`, or moving-camera stabilization.
3. Use [troubleshooting](references/troubleshooting.md) for OpenCV import errors, invalid video paths, codec/writer failures, missing frame files, hidden dead points, path/grid misuse, `MotionEstimator.update(...) is None`, or fixed-camera cropping warnings.
4. For a dependency-light local check, run:

   ```bash
   python scripts/video_smoke.py
   python scripts/camera_motion_smoke.py
   ```

   Add `--output-dir ./norfair-video-smoke` if you want to keep the tiny generated videos for visual inspection.

## Bundled scripts

- [`scripts/video_smoke.py`](scripts/video_smoke.py): tiny synthetic video round-trip with point/box overlays and a path trail.
- [`scripts/camera_motion_smoke.py`](scripts/camera_motion_smoke.py): synthetic motion-estimation and fixed-camera smoke with absolute grids and stabilized output.

## Route away

- Tracker lifecycle, `Tracker` constructor choices, distance functions, thresholds, initialization, ReID, hit counters, and core `Detection`/`TrackedObject` behavior: use `../tracking-core/SKILL.md`.
- MOTChallenge parsing, accumulators, metrics, and benchmark/evaluation reports: use `../evaluation/SKILL.md`.
- External detector integrations that download model weights or require GPU/Docker stacks: keep detector setup outside this sub-skill, then return here with already-produced Norfair detections/tracks for visualization.

## Operating stance

- Treat OpenCV (`norfair[video]` or `opencv-python`) as required for every API in this sub-skill except pure color parsing.
- Draw overlays before `Video.write(frame)`. When using `FixedCamera`, draw everything else first and call `FixedCamera.adjust_frame(...)` last.
- Prefer `draw_points` and `draw_boxes` in new code. The `draw_tracked_*` names are preserved for older snippets, but they are deprecated wrappers.
- For moving cameras, keep detection and tracker tuning in `tracking-core`; this sub-skill owns the visualization loop, masks for motion estimation, coordinate-transform usage, and debugging overlays.
