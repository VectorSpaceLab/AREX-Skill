---
name: norfair
description: "Route Norfair object tracking, video overlays, moving-camera
  stabilization, and MOTChallenge evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Norfair

Norfair is a lightweight Python library for real-time multi-object tracking. Use this skill when you need to turn detector outputs into tracked objects, draw those tracks on video, estimate camera motion, or score MOTChallenge outputs.

## Install

Choose the smallest install that matches the workflow you need:

```bash
pip install norfair
pip install norfair[video]
pip install norfair[metrics]
pip install norfair[video,metrics]
```

- `norfair` covers the core tracking APIs, distance helpers, filters, and tracker lifecycle behavior.
- `norfair[video]` adds OpenCV-backed video I/O, drawing, path rendering, and camera-motion utilities.
- `norfair[metrics]` adds MOTChallenge evaluation support through `motmetrics` and `pandas`.

For a fast environment check, run:

```bash
python scripts/check_norfair_env.py --core
python scripts/check_norfair_env.py --video
python scripts/check_norfair_env.py --metrics
```

## Route to a sub-skill

- [`sub-skills/tracking-core/SKILL.md`](sub-skills/tracking-core/SKILL.md): wrap detections in `Detection`, configure `Tracker`, choose distance functions, tune lifecycle thresholds, add embeddings, and recover identities with ReID.
- [`sub-skills/video-visualization/SKILL.md`](sub-skills/video-visualization/SKILL.md): read and write video, draw points or boxes, render paths, estimate camera motion, and stabilize moving-camera footage.
- [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md): parse MOTChallenge folders, write prediction text files, compute metrics, and compare MOTChallenge evaluation variants.

## Coverage map

- Core tracking: `Detection`, `Tracker`, `TrackedObject`, distance functions, lifecycle counters, filters, coordinate transforms, labels, embeddings, and ReID recovery.
- Video and visualization: `Video`, `VideoFromFrames`, point and box overlays, paths, camera-motion estimation, absolute-grid debugging, and fixed-camera stabilization.
- Evaluation: MOTChallenge parsing, prediction saving, accumulator flow, metrics rendering, and comparison notes.

## Start here

1. If you are unsure whether the package is installed correctly, read [`references/troubleshooting.md`](references/troubleshooting.md) and run `scripts/check_norfair_env.py`.
2. If the task is about tracker behavior, thresholds, labels, or ReID, open `sub-skills/tracking-core/SKILL.md`.
3. If the task is about OpenCV frames, overlays, paths, or camera motion, open `sub-skills/video-visualization/SKILL.md`.
4. If the task is about MOTChallenge text files or metrics, open `sub-skills/evaluation/SKILL.md`.
5. When you need to check whether this skill still matches the current checkout, read [`references/repo-provenance.md`](references/repo-provenance.md).

## Good defaults

- Start with `distance_function="euclidean"` for centroid tracking.
- Use `distance_function="iou"` for box tracking.
- Use `draw_points` for centroids or keypoints and `draw_boxes` for two-corner boxes.
- Use `TranslationTransformationGetter` with `FixedCamera`; use `HomographyTransformationGetter` for more general motion without fixed-camera stabilization.
- Use `predictions.txt` and `metrics.txt` only through the evaluation sub-skill and its bundled helper scripts.

## Public runtime files

This generated skill is self-contained. Future agents should use the bundled `references/` and `scripts/` inside this directory.
