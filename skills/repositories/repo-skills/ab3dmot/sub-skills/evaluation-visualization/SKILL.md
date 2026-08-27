---
name: evaluation-visualization
description: "Evaluate, threshold, combine, and visualize AB3DMOT KITTI and
  nuScenes tracking results."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# AB3DMOT evaluation and visualization router

Use this sub-skill when a future agent already has AB3DMOT tracking outputs and needs to evaluate, threshold, package, combine, inspect, or visualize them. It covers completed KITTI and nuScenes result folders only.

Do not use this sub-skill to prepare raw datasets, convert detections into tracker inputs, or run the tracker. Route those tasks to the data-conversion or tracking-pipeline sub-skills.

## Route by task

- KITTI local validation metrics, 3D/2D IoU choices, and KITTI test-server submission packaging: read [references/kitti-evaluation.md](references/kitti-evaluation.md).
- nuScenes result export, official local evaluation, quick validation evaluation, optional dependencies, and test-server packaging: read [references/nuscenes-evaluation.md](references/nuscenes-evaluation.md).
- Interpreting `results/<dataset>/<result_sha>/`, combined/category folders, hypothesis folders, thresholded folders, affinity output, and visualization folders: read [references/result-layout.md](references/result-layout.md).
- Failures involving result SHA names, missing `data_0`/`trk_withid_0`, threshold selection, missing nuScenes JSON, or visualization image/calibration roots: read [references/troubleshooting.md](references/troubleshooting.md).
- To generate safe shell command sequences without importing AB3DMOT or touching data, run [scripts/build_postprocess_commands.py](scripts/build_postprocess_commands.py).

## Use this route for

- Building KITTI validation metric commands for 3D IoU thresholds such as `0.25`, `0.5`, and strict Car-only `0.7`.
- Building KITTI 2D MOT commands at `0.5` IoU and preparing thresholded test-submission folders.
- Applying AB3DMOT's detector/category confidence thresholds before 2D MOT submission or qualitative visualization.
- Converting AB3DMOT nuScenes tracking output to `results_<split>.json` before official nuScenes tracking evaluation.
- Choosing between official nuScenes evaluation and the quicker KITTI-style validation diagnostic.
- Rendering image/video visualizations from `trk_withid_<hypothesis>/` result folders.

## Do not use this route for

- Creating raw KITTI or nuScenes data trees; use data-conversion first.
- Running `main.py`; use tracking-pipeline first.
- Claiming official test-set metrics without an external benchmark-server result.
- Debugging detector-row schemas before tracking; use the data-conversion validator.

## Operating assumptions

- Evaluation/visualization commands run from the root of an AB3DMOT checkout with its runtime dependencies available; the generated skill directory only provides routing and command-building helpers.
- `result_sha` is the folder basename under `results/KITTI/` or `results/nuScenes/`, for example `pointrcnn_val_H1`, `pointrcnn_test_H1`, or `megvii_val_H1`.
- Evaluation and visualization are downstream of tracking; if the expected result folder is absent, first produce the tracking results rather than changing these commands.
- Local validation metrics require local validation labels or converted nuScenes metadata. Test-set metrics require external benchmark servers because test labels are not shipped to users.

## Fast preflight

1. Confirm `results/<dataset>/<result_sha>/data_0` exists before metrics.
2. Confirm `results/<dataset>/<result_sha>/trk_withid_0` exists before visualization or confidence-threshold output checks.
3. For nuScenes official evaluation, confirm `results/<split>.json` exists or run the result-export command first.
4. Use the bundled command builder to print commands before running scripts that mutate result folders.
