---
name: training-evaluation
description: "Prepare CLAM dataset CSVs and splits, train CLAM or MIL models,
  evaluate checkpoints, and diagnose task/model/data mismatches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# CLAM Training and Evaluation

Use this sub-skill when a user needs to turn extracted CLAM feature bags into train/validation/test splits, train `CLAM_SB`, `CLAM_MB`, or MIL baselines, evaluate checkpoints, or debug task/model/data mismatches.

## Route First

- For raw whole-slide segmentation, patch coordinates, presets, or stitched QC images, use `../wsi-preprocessing/SKILL.md`.
- For ResNet50, UNI, or CONCH feature extraction and `pt_files/` creation, use `../feature-extraction/SKILL.md`.
- For attention heatmaps and interpretation from trained checkpoints, use `../heatmap-visualization/SKILL.md`.
- Stay here for dataset CSV schemas, split generation, `main.py` training, `eval.py` checkpoint evaluation, model constructor choices, and metrics outputs.

## Operating Checklist

1. Confirm the dataset CSV has `case_id`, `slide_id`, and the selected label column; `slide_id` must match feature file basenames.
2. Confirm features are arranged as `DATA_ROOT_DIR/<dataset_feature_dir>/pt_files/<slide_id>.pt` and that `--embed_dim` matches the encoder used upstream.
3. Generate or select `splits_<fold>.csv` files with `train`, `val`, and `test` columns before training.
4. For custom tasks, update the CLAM task choices and dataset constructor branches consistently in split, training, and evaluation entrypoints.
5. Train with `main.py`, matching `--task`, `--model_type`, `--subtyping`, loss flags, fold range, and split directory.
6. Evaluate with `eval.py`, matching the checkpoint directory, model flags, task branch, fold range, split files, and feature dimension.

## Bundled References

- Read `references/data-formats.md` when preparing dataset CSVs, feature folder layouts, label dictionaries, or split files.
- Read `references/training-reference.md` when assembling a `main.py` command or explaining training outputs.
- Read `references/evaluation-reference.md` when evaluating checkpoints or independent cohorts with `eval.py`.
- Read `references/model-api.md` when selecting `CLAM_SB`, `CLAM_MB`, `MIL_fc`, `MIL_fc_mc`, dataset classes, losses, or `embed_dim` values.
- Read `references/troubleshooting.md` when diagnosing missing columns, label mismatches, split paths, `--subtyping` assertions, SVM loss imports, or checkpoint shape errors.

## Bundled Scripts

- Run `scripts/clam_split_recipe.py` to validate a CLAM dataset CSV and render a safe `create_splits_seq.py` command without creating split files by default.
- Run `scripts/clam_train_eval_command_builder.py` to render safe `main.py` or `eval.py` commands, check task/model/embed-dimension consistency, and preview output paths without training or loading checkpoints.

## Safety Notes

- CLAM training, evaluation, and feature loading can require GPU memory, large `.pt` bags, valid checkpoints, and optional packages such as `smooth-topk`; bundled helpers only validate inputs and build commands.
- The CLAM source entrypoints are task-branch based. For new tasks, future agents should edit their own working CLAM copy rather than relying on hard-coded dummy tasks.
