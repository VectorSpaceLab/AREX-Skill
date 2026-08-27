---
name: planning-preprocessing
description: "Plan and preprocess prepared nnU-Net v2 datasets: fingerprint
  extraction, experiment planning, plans files, preprocessing configurations,
  worker choices, and rerun decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Planning and Preprocessing

Use this sub-skill after a dataset has already been converted and validated into nnU-Net raw format. It covers dataset fingerprints, experiment planners, plans identifiers, preprocessing configurations, normalization/resampling consequences, and inspection of `nnUNet_preprocessed` outputs.

## Route here when

- The user needs `nnUNetv2_plan_and_preprocess`, `nnUNetv2_extract_fingerprint`, `nnUNetv2_plan_experiment`, or `nnUNetv2_preprocess` commands.
- The user asks what `dataset_fingerprint.json`, `nnUNetPlans.json`, `plans_identifier`, `data_identifier`, `spacing`, `normalization_schemes`, or `preprocessor_name` means.
- The user needs to decide whether to rerun fingerprint extraction, planning, preprocessing, or only training.
- The user is choosing configurations such as `2d`, `3d_fullres`, `3d_lowres`, residual encoder planners, worker counts, progress bars, or custom plans names.

## Boundaries

- Dataset conversion, dataset IDs, `dataset.json`, labels, file endings, and raw data layout belong to `data-preparation`.
- Training, folds, checkpoints, validation, inference, and using `-p` during train/predict belong to `training-configuration`.
- Implementing custom planner, preprocessor, normalization, reader/writer, or resampling classes belongs to `customization-extension`.

## Fast paths

- New dataset, first safe pass: `nnUNetv2_plan_and_preprocess -d DATASET_ID --verify_dataset_integrity`.
- Fresh fingerprint and plans but stale preprocessed arrays: run only `nnUNetv2_preprocess -d DATASET_ID -c CONFIGS`.
- Changed target spacing, planner, preprocessor, normalization, resampling, or `data_identifier`: plan again with a distinct plans name when appropriate, then rerun preprocessing for affected configurations.
- Need generated commands without running them: use `scripts/build_plan_preprocess_command.py`.

## References

- `references/cli-reference.md` for exact CLI/API boundaries and command patterns.
- `references/plans-and-preprocessing.md` for plans files, presets, normalization, resampling, and inspection.
- `references/troubleshooting.md` for common failures and rerun decisions.
