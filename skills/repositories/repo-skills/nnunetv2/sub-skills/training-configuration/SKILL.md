---
name: training-configuration
description: "Configure and launch nnU-Net v2 training runs after
  planning/preprocessing is complete: folds, configurations, resume/validation
  flags, devices/DDP, pretrained weights, trainer selection, checkpoints, logs,
  manual splits, and command matrices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# nnU-Net v2 Training Configuration

Use this sub-skill when the user needs to train nnU-Net v2 models on already planned and preprocessed data, choose folds/configurations, recover validation exports, resume runs, select devices, or understand training outputs.

Do not use this sub-skill for dataset conversion, planning, preprocessing, inference, best-configuration selection, ensembling, or implementing new trainer subclasses. For custom trainer code, route to `customization-extension`; this sub-skill only shows how to select trainer class names in training commands.

## Fast Path

1. Confirm `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results` are set and that the dataset has been planned/preprocessed.
2. Choose a trained configuration from the dataset plans, commonly `2d`, `3d_fullres`, `3d_lowres`, or `3d_cascade_fullres`.
3. Train folds with `--npz` if model selection or ensembling may be needed later:
   ```bash
   nnUNetv2_train DATASET001_Example 3d_fullres 0 --npz
   ```
4. Train all folds by repeating folds `0` through `4`, or train one final model on all cases with fold `all` when cross-validation is not needed:
   ```bash
   nnUNetv2_train DATASET001_Example 3d_fullres all
   ```
5. For cascade training, complete `3d_lowres` first, then train `3d_cascade_fullres`.
6. Inspect outputs under `nnUNet_results/DatasetXXX_Name/TRAINER__PLANS__CONFIGURATION/fold_X/`.

## Bundled References

- `references/cli-reference.md`: exact `nnUNetv2_train` arguments, Python API mapping, flags, device/DDP semantics, and output paths.
- `references/training-workflows.md`: common training matrices, cascade ordering, manual splits, pretraining/fine-tuning, logging, and command generation.
- `references/troubleshooting.md`: failure-mode triage for missing preprocessing, cascade dependencies, `--npz` recovery, resume/validation choices, DDP, checkpoints, CPU/MPS expectations, and manual split placement.
- `scripts/plan_training_matrix.py`: prints command matrices for folds/configurations without running training.

## Command Matrix Helper

Use the bundled helper to produce reviewable shell commands before launching expensive jobs:

```bash
python sub-skills/training-configuration/scripts/plan_training_matrix.py DATASET001_Example --configs 2d 3d_fullres --folds 0 1 2 3 4 --npz
```

It only prints commands. It does not inspect data, allocate GPUs, submit cluster jobs, or run `nnUNetv2_train`.
