---
name: nnunetv2
description: "Use nnU-Net v2 for medical image segmentation workflows: dataset
  preparation, planning/preprocessing, training, inference/evaluation, model
  sharing, and customization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# nnU-Net v2

Use this skill when the user needs practical help with nnU-Net v2, the self-configuring medical image segmentation framework exposed by the `nnunetv2` Python package and `nnUNetv2_*` command-line tools.

## Quick Start

1. Confirm the package and core commands are available:
   ```bash
   python scripts/check_nnunet_setup.py --require-commands
   ```
2. Confirm the nnU-Net storage environment variables are set for the requested workflow: `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results`.
3. Route to the focused sub-skill before giving detailed commands; nnU-Net workflows are order-dependent.
4. Prefer CLI commands for user workflows and use Python APIs for programmatic integration, dry-run command generation, or validation helpers.

## Route by Task

- Dataset folders, `dataset.json`, labels, regions, ignore labels, file endings, MSD/v1 conversion, or path variables: use `sub-skills/data-preparation/SKILL.md`.
- Fingerprint extraction, experiment planning, preprocessing, plans files, residual encoder presets, or rerun decisions: use `sub-skills/planning-preprocessing/SKILL.md`.
- Training folds/configurations, `--npz`, validation-only reruns, resume, checkpoints, device/DDP, pretrained weights, logging, or manual splits: use `sub-skills/training-configuration/SKILL.md`.
- Prediction, `predict_from_modelfolder`, ensembling, postprocessing, evaluation, best-configuration selection, model zip import/export/download, or inference troubleshooting: use `sub-skills/inference-evaluation/SKILL.md`.
- Custom trainers, planners, preprocessors, normalization, image I/O, class discovery, `nnUNet_extTrainer`, or custom-trainer model portability: use `sub-skills/customization-extension/SKILL.md`.

## End-to-End Workflow

For a new dataset, the normal route is:

```bash
# 1) Prepare raw dataset in nnU-Net format.
python sub-skills/data-preparation/scripts/validate_dataset_json.py /path/to/nnUNet_raw/Dataset123_MyDataset --check-files

# 2) Plan and preprocess.
nnUNetv2_plan_and_preprocess -d 123 --verify_dataset_integrity

# 3) Train folds; use --npz if model selection/ensembling may be needed.
nnUNetv2_train 123 3d_fullres 0 --npz

# 4) Select/evaluate/predict after training artifacts exist.
nnUNetv2_find_best_configuration 123 -c 2d 3d_fullres
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d 123 -c 3d_fullres
```

Read `references/workflow-overview.md` for ordering, prerequisites, and cross-skill handoffs.

## Core Commands

- `nnUNetv2_plan_and_preprocess` runs dataset fingerprinting, experiment planning, and preprocessing together.
- `nnUNetv2_extract_fingerprint`, `nnUNetv2_plan_experiment`, and `nnUNetv2_preprocess` run those stages separately.
- `nnUNetv2_train` trains a dataset/configuration/fold, including validation and resume modes.
- `nnUNetv2_predict` predicts from stored nnU-Net results; `nnUNetv2_predict_from_modelfolder` predicts from an explicit model folder.
- `nnUNetv2_find_best_configuration`, `nnUNetv2_ensemble`, `nnUNetv2_apply_postprocessing`, and evaluation commands handle model selection and validation outputs.
- `nnUNetv2_export_model_to_zip`, `nnUNetv2_install_pretrained_model_from_zip`, and `nnUNetv2_download_pretrained_model_by_url` move model bundles.

Read `references/cli-map.md` for command ownership and when to inspect `-h`.

## References and Helpers

- `references/repo-provenance.md`: source version, evidence paths, and refresh baseline.
- `references/workflow-overview.md`: complete workflow order and handoffs between sub-skills.
- `references/cli-map.md`: command map, owning sub-skill, and safe verification approach.
- `references/troubleshooting.md`: cross-cutting install, path, dependency, GPU, and workflow-order failures.
- `scripts/check_nnunet_setup.py`: safe import, command, environment-variable, and optional Torch backend check.

## Operating Rules

- Do not skip dataset validation; malformed `dataset.json`, file endings, labels, or channel suffixes usually fail later during planning or prediction.
- Use `--npz` during training if later `nnUNetv2_find_best_configuration` or probability ensembling may be needed; use `--val --npz` to recover validation probabilities for already-trained folds.
- Treat training, preprocessing, full inference, benchmarks, and integration scripts as potentially expensive; use helper scripts here for checks and command generation, not for long runs.
- When a model uses a custom trainer, ensure the class is importable on every machine that will continue training or run inference.
- Keep generated commands generic; never rely on the original source checkout being present.
