---
name: postprocessing-3d-video-exports
description: "Route DeepLabCut post-processing, video utilities, 3D
  calibration/triangulation, and model export requests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Post-processing, 3D, and export router

Use this sub-skill when the request starts from analyzed pose outputs, refined labels, rendered videos, 3D stereo data, or exportable model weights.

## Handle here
- Smooth or inspect analyzed predictions with `filterpredictions`
- Detect outliers and expand labels with `extract_outlier_frames` or `find_outliers_in_raw_data`
- Merge corrected labels with `merge_datasets`
- Render labels, trajectory plots, and skeleton measurements
- Check, crop, downsample, or shorten videos before visualization
- Calibrate stereo cameras, verify undistortion, triangulate, and render 3D videos
- Export portable PyTorch weights with `export_model`

## Route elsewhere first when
- You still need first-pass training, evaluation, or raw video analysis -> `../pytorch-training-evaluation-inference/SKILL.md`
- You need detections-to-tracklets, stitching, or re-identification -> `../multi-animal-tracking/SKILL.md`
- You need SuperAnimal or pretrained-model inference/adaptation -> `../model-zoo-superanimal/SKILL.md`
- You need project setup, frame labeling, or training-dataset creation -> `../install-and-project-setup/SKILL.md` or `../data-labeling-and-training-datasets/SKILL.md`

## Default decision order
1. Confirm the analysis folder, shuffle, trainingsetindex, and track method that produced the outputs.
2. Decide whether the task is 2D cleanup, refinement, video prep, 3D, or export.
3. Use the smallest API that touches only the needed files.
4. Keep `destfolder` and filename pairing consistent across filter, label, plot, and triangulation steps.

## Common outputs
- Analyzed predictions: `.h5` and optional `.csv`
- Filtered predictions: `*_filtered.h5` and optional `*_filtered.csv`
- Refined frames: corrected labels plus `MachineLabelsRefine.h5` during refinement
- Labeled videos and trajectory plots
- Skeleton summaries: `*_skeleton.h5` and optional `.csv`
- 3D triangulation outputs and metadata
- Exported model bundles under `exported-models-pytorch/`

## Bundled helper
- `scripts/collect_video_inventory.py` prints a JSON inventory of candidate video files, extensions, and exclusion results without modifying anything.

## Details
- API-level notes live in `references/api-reference.md`
- Workflow ordering and filename expectations live in `references/workflows.md`
- Failure modes and recovery cues live in `references/troubleshooting.md`
