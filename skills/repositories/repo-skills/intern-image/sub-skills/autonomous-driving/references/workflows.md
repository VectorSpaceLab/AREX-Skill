# Autonomous-Driving Workflows

## Purpose

Read this when choosing or planning InternImage autonomous-driving baselines. The bundled helper prints safe shell templates only; it never trains, evaluates, downloads, preprocesses, or mutates a checkout.

## Baseline selection

| User task | Select | Core model/config evidence | Data prerequisite | Runtime caveat |
| --- | --- | --- | --- | --- |
| 3D occupancy prediction on nuScenes/Occ3D-style data | `occupancy` | BEVFormerOcc with InternImage-S in `projects/configs/bevformer/bevformer_intern-s_occ.py`; base and small variants are also bundled. | `data/occ3d-nus/` with Occ3D/nuScenes data, CAN bus expansion, maps, `gts/annotations.json`, and generated `occ_infos_temporal_{train,val}.pkl`. | mmdet3d 0.18.x stack, CUDA, DCNv3, checkpoints, and multi-GPU memory are normally required. |
| Online HD map construction | `hd-map` | VectorMapNet with InternImage-S in `src/configs/vectormapnet_intern.py`; `src/configs/vectormapnet.py` is the baseline fallback. | Argoverse 2 challenge data converted into train/val/test annotation JSON and image roots matching the local environment. | The source config contained site-specific dataset placeholders; use `--cfg-option` overrides or a local config copy before execution. |
| OpenLane-V2 scene-structure/topology challenge | `openlane` | ROAD_BEVFormer with InternImage-S in `plugin/mmdet3d/configs/internimage-s.py`; baseline configs include `baseline.py` and `baseline_large.py`. | `data/OpenLane-V2/` hierarchy plus preprocessed `data_dict_subset_A_{train,val}.pkl`. | mmdet3d 1.0.0rc6-era stack, seven cameras, OpenLane-V2 devkit, CUDA, and DCNv3 for InternImage. |

## Command-builder usage

Use `<SKILL_DIR>` as the directory containing this sub-skill. Use `<REPO_ROOT>` as the InternImage checkout you want to operate on. The helper is dry-run only; it prints shell commands and does not execute them.

List the bundled baselines and config variants:

```bash
python <SKILL_DIR>/scripts/build_autonomous_command.py --list
```

Build the documented Occupancy Prediction training plan:

```bash
python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline occupancy --mode train --variant intern-s --gpus 8 \
  --repo-root '<REPO_ROOT>'
```

Build an occupancy evaluation plan with the F-score flag:

```bash
python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline occupancy --mode test --variant intern-s --gpus 8 \
  --repo-root '<REPO_ROOT>' --checkpoint '<CHECKPOINT.pth>' \
  --eval-metric bbox --eval-fscore
```

Build the InternImage VectorMapNet HD-map training plan with local data overrides:

```bash
python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline hd-map --mode train --variant intern --gpus 8 \
  --repo-root '<REPO_ROOT>' \
  --cfg-option data.train.ann_file='<train_annotations.json>' \
  --cfg-option data.train.root_path='<train_root>'
```

Plan HD-map validation or test-set formatting:

```bash
python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline hd-map --mode test --variant intern --gpus 8 \
  --repo-root '<REPO_ROOT>' --checkpoint '<CHECKPOINT.pth>' \
  --split val --operation eval

python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline hd-map --mode test --variant intern --gpus 8 \
  --repo-root '<REPO_ROOT>' --checkpoint '<CHECKPOINT.pth>' \
  --split test --operation format
```

Plan OpenLane-V2 training and validation with submission dumping:

```bash
python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline openlane --mode train --variant intern-s --gpus 8 \
  --repo-root '<REPO_ROOT>'

python <SKILL_DIR>/scripts/build_autonomous_command.py \
  --baseline openlane --mode test --variant intern-s --gpus 8 \
  --repo-root '<REPO_ROOT>' --checkpoint '<CHECKPOINT.pth>' \
  --operation eval --dump-dir '<submission_dir>' \
  --visualization-dir '<vis_dir>'
```

For machine-readable planning, add `--format json`.

`--dry-run` is accepted as an explicit no-op guard for people who want to say the command is plan-only; the helper is already dry-run only.

## What the helper preserves from source launchers

| Source artifact label | Bundled decision | Preserved behavior | Intentional omissions |
| --- | --- | --- | --- |
| Occupancy train/test launchers | Adapted into command templates | Distributed launch uses `torch.distributed.launch`, `--launcher pytorch`, configurable `NNODES`, `NODE_RANK`, `MASTER_ADDR`, and port; the training template also preserves the source deterministic default. | Does not run training or infer local data paths. |
| Online HD-map train/test launchers | Adapted into command templates | Distributed launch mirrors the source shell wrappers, including config overrides for local data roots and the `--split val|test` gate on testing. | Does not include site-specific Slurm wrappers. |
| OpenLane-V2 train/test launchers | Adapted into command templates | Distributed launch mirrors the source wrapper, including `--seed 0` on training and `--eval-options dump=True dump_dir=...` for submission dumps. | Does not build DCNv3 or create symlinks into another repo checkout. |
| OpenLane-V2 dataset dumping path | Referenced through template notes | The helper carries the submission-dump and visualization options through to the source test parser. | It does not execute the dump, and the source evaluator/import issue still has to be patched before full evaluation. |

## Baseline-specific preparation reminders

### Occupancy Prediction

- Install a compatible mmdet3d 0.18.x/OpenMMLab stack, PyTorch/CUDA, timm, NumPy 1.22-era dependencies, and DCNv3 for the BEVFormer InternImage backbone.
- Prepare the Occ3D/nuScenes hierarchy and run the data conversion equivalent to:

```bash
python tools/create_data.py occ --root-path ./data/occ3d-nus --out-dir ./data/occ3d-nus \
  --extra-tag occ --version v1.0-trainval --canbus ./data --occ-path ./data/occ3d-nus
```

- Expected generated metadata names include `occ_infos_temporal_train.pkl` and `occ_infos_temporal_val.pkl` because the selected configs point to those names.

### Online HD Map Construction

- Install a mmdet3d 1.0.0rc6-era stack with mmcv-full 1.5.x, mmdet 2.28.x, mmsegmentation 0.29.x, PyTorch/CUDA, timm, and DCNv3.
- Override dataset annotation and root-path fields for the local Argoverse 2 challenge data. Do not rely on source placeholder paths.
- The InternImage config uses an InternImage-S checkpoint URL in `init_cfg`; decide ahead of time whether your environment can download it or whether you will substitute a local checkpoint.

### OpenLane-V2

- Install the OpenLane-V2 devkit (`openlanev2==0.1.0` in the inspected source) plus the mmdet3d plugin stack before model training/evaluation.
- Use `data/OpenLane-V2` as the data and metadata root unless you intentionally change `data_root` and `meta_root` in the config.
- If you need a pickle submission, run the command builder with `--dump-dir`, then validate any JSON intermediate with the bundled validator before conversion/upload.

## Stop conditions

Stop and ask for environment or data decisions before executing a generated command when any of these are unknown: dataset availability/licensing, checkpoint availability, CUDA/GPU count, DCNv3 build status, OpenMMLab version family, write location for work dirs or dumps, or whether external downloads are allowed.
