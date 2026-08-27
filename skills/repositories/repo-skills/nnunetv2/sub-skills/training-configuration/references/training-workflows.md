# Training Workflows

Use these workflows after dataset conversion, planning, and preprocessing have completed.

## Choose a Training Matrix

A training matrix is the Cartesian product of datasets, configurations, folds, trainers, plans, and flags. Keep it explicit before launching long jobs.

Recommended columns:

- dataset: integer ID or `DatasetXXX_Name`.
- configuration: planned configuration, for example `2d` or `3d_fullres`.
- fold: `0` through `4`, or `all`.
- trainer: usually `nnUNetTrainer` unless testing a known variant.
- plans: usually `nnUNetPlans` unless using transferred/custom plans.
- validation export: whether `--npz` is required.
- device strategy: one fold per GPU, DDP, CPU/MPS smoke test, or cluster submission wrapper.

For model selection or ensembling, train every candidate configuration/fold with `--npz` or regenerate validation with `--val --npz` later.

## Common Matrices

One configuration, all cross-validation folds:

```bash
for fold in 0 1 2 3 4; do
  nnUNetv2_train Dataset001_Example 3d_fullres "$fold" --npz
done
```

Two configurations, all cross-validation folds:

```bash
for config in 2d 3d_fullres; do
  for fold in 0 1 2 3 4; do
    nnUNetv2_train Dataset001_Example "$config" "$fold" --npz
  done
done
```

Final model on all cases after the preferred setup is known:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres all
```

Quick trainer smoke test with checkpointing disabled:

```bash
nnUNetv2_train Dataset001_Example 2d 0 -tr nnUNetTrainer_5epochs --disable_checkpointing
```

Do not use `--disable_checkpointing` for runs that must resume, validate later, or provide production checkpoints.

## Generate Commands Without Running Training

The bundled helper prints command matrices:

```bash
python sub-skills/training-configuration/scripts/plan_training_matrix.py Dataset001_Example \
  --configs 2d 3d_fullres \
  --folds 0 1 2 3 4 \
  --npz
```

Add GPU assignment comments for one-fold-per-GPU review:

```bash
python sub-skills/training-configuration/scripts/plan_training_matrix.py Dataset001_Example \
  --configs 3d_fullres \
  --folds 0 1 2 3 4 \
  --npz \
  --gpu-ids 0 1
```

Generate DDP commands for a single fold at a time:

```bash
python sub-skills/training-configuration/scripts/plan_training_matrix.py Dataset001_Example \
  --configs 3d_fullres \
  --folds 0 \
  --npz \
  --num-gpus 2
```

The helper does not check whether the dataset was preprocessed or whether the configuration exists; it is a planning aid only.

## Cascade Training

Cascade training requires low-resolution predictions before full-resolution cascade training.

Per fold:

```bash
nnUNetv2_train Dataset001_Example 3d_lowres 0 --npz
nnUNetv2_train Dataset001_Example 3d_cascade_fullres 0 --npz
```

All folds:

```bash
for fold in 0 1 2 3 4; do
  nnUNetv2_train Dataset001_Example 3d_lowres "$fold" --npz
  nnUNetv2_train Dataset001_Example 3d_cascade_fullres "$fold" --npz
done
```

Do not start `3d_cascade_fullres` until the matching `3d_lowres` fold exists. If the planner did not create `3d_lowres`, the cascade is not available for that dataset.

## Recover Validation Probabilities

If folds were trained without `--npz`, regenerate validation probabilities before model selection:

```bash
for fold in 0 1 2 3 4; do
  nnUNetv2_train Dataset001_Example 3d_fullres "$fold" --val --npz
done
```

Use `--val_best` only when the user intentionally wants validation from `checkpoint_best.pth`. It writes to the same validation folder as regular validation, so document the choice externally if comparing both.

## Resume Interrupted Runs

Continue an interrupted training run:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 --c --npz
```

Notes:

- Keep `--npz` if validation probabilities are desired at the end of the resumed run.
- Do not combine `--c` with `--val`.
- Do not combine `--c` with `-pretrained_weights`; pretrained weights are only for initializing new training.
- If no checkpoint exists, nnU-Net warns and starts a new run.

## One Fold Per GPU vs DDP

Prefer independent fold launches when multiple folds/configurations are available:

```bash
CUDA_VISIBLE_DEVICES=0 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz
CUDA_VISIBLE_DEVICES=1 nnUNetv2_train Dataset001_Example 3d_fullres 1 --npz
CUDA_VISIBLE_DEVICES=2 nnUNetv2_train Dataset001_Example 3d_fullres 2 --npz
CUDA_VISIBLE_DEVICES=3 nnUNetv2_train Dataset001_Example 3d_fullres 3 --npz
```

Use DDP when accelerating one fold is more important than running multiple independent folds:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz -num_gpus 4
```

DDP is CUDA-only. `-device` selects `cuda`, `cpu`, or `mps`; it does not select GPU IDs.

## Manual Splits

Manual cross-validation splits are stored as:

```text
nnUNet_preprocessed/DatasetXXX_Name/splits_final.json
```

The file is a JSON list. Each list item represents one fold and contains `train` and `val` arrays of case identifiers without file extensions:

```json
[
  {
    "train": ["case_000", "case_001"],
    "val": ["case_002"]
  },
  {
    "train": ["case_002", "case_001"],
    "val": ["case_000"]
  }
]
```

Create the preprocessed dataset folder first by planning/preprocessing, then place `splits_final.json` in that dataset folder before training. nnU-Net uses an existing split file instead of generating default splits.

## Pretraining and Fine-Tuning Basics

nnU-Net supports supervised pretraining by training a compatible network on a pretraining dataset, then initializing fine-tuning with compatible checkpoint weights.

High-level flow:

1. Plan and preprocess the fine-tuning dataset.
2. Extract the fingerprint for the pretraining dataset if needed.
3. Move the fine-tuning plans to the pretraining dataset with a custom target plans identifier.
4. Preprocess the pretraining dataset with that transferred plans identifier.
5. Train the pretraining dataset, often with fold `all`:
   ```bash
   nnUNetv2_train Dataset010_Pretrain 3d_fullres all -p TransferredPlans
   ```
6. Initialize fine-tuning with the pretraining checkpoint:
   ```bash
   nnUNetv2_train Dataset011_Finetune 3d_fullres 0 -pretrained_weights /path/to/checkpoint_final.pth --npz
   ```

When loading pretrained weights, nnU-Net transfers matching non-segmentation layers and skips segmentation layers. The checkpoint must be compatible with the target network topology. For custom fine-tuning schedules or new trainer subclasses, route to `customization-extension`.

## Logging and Run Review

For each fold, inspect:

- `training_log_*.txt` for startup settings, epochs, warnings, and resume behavior.
- `progress.png` for losses, learning rate, and Dice trends.
- `debug.json` for plans/trainer runtime details.
- `validation/summary.json` for validation metrics.
- `validation/*.npz` when `--npz` was requested.

Optional W&B logging is controlled by environment variables and does not replace local outputs. Local outputs remain the source of truth for downstream nnU-Net tooling.
