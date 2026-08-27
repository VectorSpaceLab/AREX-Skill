---
name: dataset-preparation
description: "Validate nuScenes + CAN-bus layout and the generated BEVFormer
  temporal annotation files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dataset Preparation

Use this sub-skill when a task depends on the nuScenes raw tree, CAN-bus expansion, or the temporal annotation files consumed by BEVFormer and BEVFormerV2.

## Covers

- nuScenes folder layout checks for the raw `samples/`, `sweeps/`, `maps/`, and version folders.
- CAN-bus expansion placement and the pose metadata it feeds.
- Generated `nuscenes_infos_temporal_train.pkl`, `nuscenes_infos_temporal_val.pkl`, and `nuscenes_infos_temporal_test.pkl`.
- `data_root` / `ann_file` wiring for camera-only BEVFormer configs.
- Metadata keys emitted by `CustomNuScenesDataset` and `CustomNuScenesDatasetV2`.

## Routes elsewhere

- Model, backbone, transformer, or other config knobs belong in installation-and-configs.
- Distributed training, evaluation, checkpoints, or FP16 launch commands belong in training-and-evaluation.
- Log analysis, benchmark, or visualization tasks belong in analysis-and-utilities.

## Start here

1. Read [nuScenes layout notes](references/nuscenes-data.md).
2. Read [data format notes](references/data-formats.md).
3. Read [troubleshooting notes](references/troubleshooting.md).
4. Run [the bundled layout checker](scripts/check_bevformer_nuscenes_layout.py).
