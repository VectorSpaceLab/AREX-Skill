---
name: tracking-pipeline
description: "Run AB3DMOT tracking safely and use the core AB3DMOT tracker APIs
  for KITTI and nuScenes 3D MOT workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# tracking-pipeline

Use this sub-skill when a task is about running AB3DMOT tracking, constructing a safe `main.py` command, understanding tracker configuration, or calling the `AB3DMOT.track` API directly.

## Read first

- For command-level tracking workflows, dataset prerequisites, category loops, and output folders, read [references/tracking-workflow.md](references/tracking-workflow.md).
- For direct API usage, synthetic smoke behavior, `AB3DMOT.track`, `Box3D`, matching, and Kalman filter details, read [references/api-reference.md](references/api-reference.md).
- For YAML defaults, CLI override behavior, detector/category compatibility, and config pitfalls, read [references/configuration.md](references/configuration.md).
- For common tracking failures and recovery steps, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled scripts

- [scripts/build_tracking_command.py](scripts/build_tracking_command.py) builds explicit, non-running `main.py` commands and prints the expected input/result folder names without importing AB3DMOT.
- [scripts/smoke_track_synthetic.py](scripts/smoke_track_synthetic.py) runs a no-dataset one-frame API smoke. Pass `--repo-root /path/to/AB3DMOT` and, when Xinshuo is external, `--toolbox-root /path/to/Xinshuo_PyToolbox`; the helper injects both paths before importing.

## Boundaries

This sub-skill owns:

- `main.py` flags: `--dataset`, `--split`, and `--det_name`.
- Config fields that affect tracking: `save_root`, `dataset`, `split`, `det_name`, `cat_list`, `score_threshold`, `num_hypo`, `ego_com`, `vis`, and `affi_pro`.
- KITTI and nuScenes detector/category compatibility for tracking.
- Result-directory naming, category-specific tracking, combined results, affinity outputs, and logs.
- Direct use of `AB3DMOT`, `AB3DMOT.track`, `Box3D`, matching, and the Kalman filter state model.

Use sibling skills for neighboring concerns:

- Data download, raw nuScenes conversion, detector-result conversion, and detection schema repair belong to [../data-conversion/SKILL.md](../data-conversion/SKILL.md).
- Metrics, confidence thresholding, result export, server submission, and visualization belong to [../evaluation-visualization/SKILL.md](../evaluation-visualization/SKILL.md).

## Fast decisions

- For KITTI PointRCNN validation, use explicit flags: `python main.py --dataset KITTI --split val --det_name pointrcnn`.
- Do not run bare `python main.py` unless the task intentionally uses the nuScenes config default.
- If the user is unsure which input folders/results will be used, run the bundled command builder first.
- If the user wants to embed AB3DMOT in another Python loop, start with the API reference and synthetic smoke script instead of the dataset-level CLI.
- If full tracking data is missing, do not treat detector text files as enough; route back to data-conversion layout checks.

## Minimal checks before running tracking

1. `python main.py --help` succeeds in the target runtime.
2. The dataset config has the intended `split`, `det_name`, `cat_list`, and `save_root`.
3. Category-specific detection folders exist for every configured category.
4. The full tracking data root contains calibration, image frame lists, and ego-motion/OXTS data for the split.
5. The result root has enough write space; tracking writes per-frame files, affinity matrices, logs, and combined category outputs.
