---
name: data-preparation
description: "Prepare and validate UniAD nuScenes, CAN bus, map, info-PKL, and
  motion-anchor data layout without launching training or evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# UniAD data-preparation router

Use this sub-skill when the user needs to prepare, validate, or troubleshoot the data assets required by UniAD on nuScenes:

- raw nuScenes layout under `data/nuscenes/`, including CAN bus and map extensions;
- temporal info PKLs under `data/infos/`;
- the stage-2/E2E motion-anchor file under `data/others/`;
- safe command synthesis for UniAD's nuScenes info generation workflow.

Do **not** launch training, evaluation, visualization, or model editing from here.

## Route boundaries

- Training, evaluation, checkpoint, GPU, distributed, or SLURM launch questions: route to `training-evaluation`.
- Model/config architecture, task heads, queue lengths, plugin classes, or registry questions: route to `config-and-model-architecture`.
- Result pickle interpretation, rendering, videos, or visualization commands: route to `visualization-and-results`.

## Operating procedure

1. Identify the intended split/version: full `v1.0` trainval/test, trainval-only, test-only, or `v1.0-mini`.
2. Identify the intended UniAD stage: BEVFormer/stage-1 versus stage-2/E2E. Stage-2/E2E requires `data/others/motion_anchor_infos_mode6.pkl`.
3. Validate the local layout with `scripts/check_uniad_data_layout.py` before constructing train/eval commands elsewhere.
4. If info PKLs must be generated, synthesize the command with `scripts/build_data_command.py`; do not run a full conversion unless the user has confirmed the raw nuScenes/CAN bus/map assets and runtime dependencies are present.
5. Warn users that generated PKLs can embed root-prefixed paths. If a generated PKL stores paths such as `data/nuscenes/...` or absolute dataset paths, the active UniAD config may need `data_root = ""` instead of the default `data_root = "data/nuscenes/"`.

## Bundled references

- `references/data-preparation.md` — layout, download choices, info-generation command semantics, and config path cautions.
- `references/data-formats.md` — expected PKL, CAN bus, map, raw-sensor, and motion-anchor contents.
- `references/troubleshooting.md` — symptoms and fixes for missing directories, missing PKLs, motion anchors, root-path mismatches, network/download limits, and split confusion.

## Bundled scripts

- `scripts/check_uniad_data_layout.py` — self-contained dry validation of the expected data layout and common PKL path-root risk.
- `scripts/build_data_command.py` — self-contained dry command renderer adapted from UniAD's data conversion wrapper semantics.
