# Training Configuration Troubleshooting

Use this guide to diagnose training launch and output issues. It assumes dataset conversion, planning, and preprocessing should already be complete.

## Missing Preprocessed Data

Symptoms:

- Training fails while loading `dataset.json` or `nnUNetPlans.json`.
- The selected plans identifier cannot be found.
- The dataset ID/name is rejected or cannot be converted to a dataset name.

Checks:

- Confirm `nnUNet_preprocessed` points to the intended preprocessed data root.
- Confirm `nnUNet_preprocessed/DatasetXXX_Name/dataset.json` exists.
- Confirm `nnUNet_preprocessed/DatasetXXX_Name/nnUNetPlans.json` exists, or pass the actual plans identifier with `-p`.
- If using an integer dataset ID, confirm it maps to an existing `DatasetXXX_Name` folder.

Fix:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 -p nnUNetPlans --npz
```

If planning/preprocessing never ran, route back to the planning/preprocessing workflow rather than trying to fix training flags.

## Configuration Not Available

Symptoms:

- A configuration name such as `3d_lowres` or `3d_cascade_fullres` fails for one dataset.
- The requested configuration is absent from the plans.

Checks:

- Inspect the dataset plans or prior planning output to see which configurations were created.
- Do not assume every dataset has `2d`, `3d_fullres`, `3d_lowres`, and `3d_cascade_fullres`.

Fix:

- Train only configurations present in the plans.
- For cascades, require both `3d_lowres` and `3d_cascade_fullres`.

## Cascade Order Problems

Symptoms:

- `3d_cascade_fullres` starts but cannot find prior-stage predictions.
- Validation or training complains about missing next-stage inputs.

Cause:

- The matching `3d_lowres` fold was not completed before `3d_cascade_fullres`.

Fix:

```bash
nnUNetv2_train Dataset001_Example 3d_lowres 0 --npz
nnUNetv2_train Dataset001_Example 3d_cascade_fullres 0 --npz
```

Repeat the low-resolution-before-cascade order for each fold.

## Trained Without `--npz`

Symptoms:

- Automatic model selection or ensembling cannot find validation probability files.
- `validation/summary.json` exists but `validation/*.npz` files are missing.

Fix:

```bash
for fold in 0 1 2 3 4; do
  nnUNetv2_train Dataset001_Example 3d_fullres "$fold" --val --npz
done
```

Notes:

- `--val` requires completed training and validates `checkpoint_final.pth` by default.
- Use `--val_best` only when intentionally validating `checkpoint_best.pth`; it reuses the same validation folder.

## Resume vs Validation Choices

Symptoms:

- Command fails with a mutual-exclusion assertion.
- A user tries to continue training and only run validation in the same command.
- A user tries to continue training while loading pretrained weights.

Rules:

- Use `--c` to resume training.
- Use `--val` to run validation only.
- Do not combine `--c` with `--val`.
- Do not combine `--c` with `-pretrained_weights`.

Resume:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 --c --npz
```

Validation-only recovery:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 --val --npz
```

If `--c` cannot find a checkpoint, nnU-Net warns and starts new training. Check the output folder before assuming a run resumed.

## GPU Selection vs DDP

Symptoms:

- Training uses the wrong GPU.
- DDP fails on CPU or MPS.
- User passes `-device cuda:1` or expects `-device` to select a GPU ID.

Rules:

- `-device` accepts only `cuda`, `cpu`, or `mps`.
- Select GPU IDs with `CUDA_VISIBLE_DEVICES`.
- `-num_gpus N` starts CUDA DDP for one fold/configuration.
- DDP requires `-device cuda`; it is not implemented for CPU or MPS.

Single selected GPU:

```bash
CUDA_VISIBLE_DEVICES=1 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz
```

DDP across two visible GPUs:

```bash
CUDA_VISIBLE_DEVICES=0,1 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz -num_gpus 2
```

If the goal is five-fold cross-validation on a multi-GPU machine, prefer independent fold launches before DDP unless the user specifically needs one fold accelerated.

## Checkpoint and Output Path Confusion

Symptoms:

- User cannot find checkpoints or validation outputs.
- Resume starts a new run unexpectedly.
- Validation says training is not finished.

Expected layout:

```text
nnUNet_results/DatasetXXX_Name/TRAINER__PLANS__CONFIGURATION/fold_X/
```

Look for:

- `checkpoint_latest.pth` during training.
- `checkpoint_final.pth` after completed training.
- `checkpoint_best.pth` when best-checkpoint tracking has saved one.
- `validation/summary.json` after validation.
- `validation/*.npz` after validation with `--npz`.

Fixes:

- Match the exact trainer, plans, configuration, and fold in the path.
- If a custom trainer or plans identifier was used, the output folder name changes.
- If checkpointing was disabled, do not expect resumable checkpoints.

## CPU and MPS Expectations

Symptoms:

- CPU training is extremely slow.
- MPS behavior differs from CUDA.
- User expects CPU/MPS to be production-equivalent to CUDA.

Guidance:

- CUDA is the normal production path for nnU-Net training.
- CPU can be useful for tiny smoke tests but is usually too slow for full runs.
- MPS is selectable but should be treated cautiously for performance and compatibility.
- DDP is CUDA-only.

For a quick syntax or trainer smoke test, use a short trainer variant and avoid production assumptions:

```bash
nnUNetv2_train Dataset001_Example 2d 0 -tr nnUNetTrainer_5epochs -device cpu --disable_checkpointing
```

## Manual Split Placement

Symptoms:

- Training ignores a custom split.
- Fold count or train/validation cases do not match the intended split.

Required placement:

```text
nnUNet_preprocessed/DatasetXXX_Name/splits_final.json
```

Required structure:

```json
[
  {"train": ["case_000", "case_001"], "val": ["case_002"]}
]
```

Checks:

- Place the file in the preprocessed dataset folder, not the raw dataset folder or results folder.
- Use case identifiers, not image filenames with `_0000.nii.gz` suffixes.
- Ensure the list contains the folds the user plans to train.
- Create or replace the split file before launching training.

## Pretrained Weight Compatibility

Symptoms:

- Loading pretrained weights fails with missing keys or shape mismatches.
- User attempts to use pretrained weights while resuming.

Rules:

- Pretrained weights initialize a new training run and cannot be combined with `--c`.
- The network topology must be compatible; transferred plans are the recommended route for supervised pretraining across datasets.
- nnU-Net loads matching non-segmentation layers and skips segmentation layers.

Fine-tuning command:

```bash
nnUNetv2_train Dataset011_Finetune 3d_fullres 0 -pretrained_weights /path/to/checkpoint_final.pth --npz
```

If compatibility fails, revisit the pretraining/fine-tuning plan alignment rather than forcing checkpoint loading.

## Slow Training or Suspicious Epoch Times

Symptoms:

- Epochs are much slower than expected.
- GPU utilization is low.
- Data loading appears to bottleneck training.

Checks:

- Compare a normal short benchmark trainer with a no-data-loading benchmark trainer.
- Confirm CUDA/PyTorch installation matches the GPU and driver stack.
- Confirm preprocessed data lives on fast local SSD/NVMe storage.
- Inspect CPU augmentation worker behavior and `nnUNet_n_proc_DA` if data loading is the bottleneck.
- Avoid network filesystems for high-throughput preprocessed arrays when possible.

Benchmark trainer examples:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 -tr nnUNetTrainerBenchmark_5epochs
nnUNetv2_train Dataset001_Example 3d_fullres 0 -tr nnUNetTrainerBenchmark_5epochs_noDataLoading
```
