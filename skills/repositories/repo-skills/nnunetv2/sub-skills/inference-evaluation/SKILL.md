---
name: inference-evaluation
description: "Run nnU-Net v2 prediction from dataset/results or explicit model
  folders, cascades, TTA/tiling/device/process controls, ensembling,
  postprocessing, evaluation, best-configuration selection, model sharing, and
  inference troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# nnU-Net v2 Inference and Evaluation

Use this sub-skill after a trained, installed, exported, downloaded, or otherwise available nnU-Net v2 model exists and the task is to generate predictions, compare configurations, ensemble outputs, evaluate segmentations, apply postprocessing, or move models between environments.

## Route here for

- Running `nnUNetv2_predict` from `nnUNet_results` with dataset id/name, trainer, plans, configuration, folds, checkpoint, device, TTA, tiling, process, and split-batch flags.
- Running `nnUNetv2_predict_from_modelfolder` when the model folder is explicit or `nnUNet_results` is unavailable.
- Providing previous-stage predictions for cascaded models with `-prev_stage_predictions`.
- Saving probability maps for downstream `nnUNetv2_ensemble` and applying `postprocessing.pkl`.
- Evaluating predictions with `nnUNetv2_evaluate_folder` or `nnUNetv2_evaluate_simple`, including ignore labels and partial-prediction `--chill` behavior.
- Selecting the best trained configuration with `nnUNetv2_find_best_configuration` after validation probabilities exist.
- Exporting, installing, downloading, or sharing trained/pretrained models, including custom-trainer availability requirements.

## Do not handle here

- Creating dataset folders, channel names, labels, or inference input naming from scratch: use `data-preparation`.
- Planning, preprocessing, experiment planners, or fingerprints: use `planning-preprocessing`.
- Training folds, validation reruns, `--npz` recovery, checkpoint creation, or trainer selection for training: use `training-configuration`.
- Implementing custom trainer subclasses or extension code: use `customization-extension`; this sub-skill only explains how inference locates custom trainer classes.

## Fast Path

1. Confirm the model exists and matches the input dataset: trained result folder with `dataset.json`, `plans.json`, and requested `fold_*` checkpoints, or an explicit model folder with the same files.
2. Check inference image filenames before running expensive prediction:
   ```bash
   python sub-skills/inference-evaluation/scripts/check_inference_inputs.py INPUT_FOLDER MODEL_OR_DATASET_JSON
   ```
3. Use `nnUNetv2_predict` when the model is in `nnUNet_results`:
   ```bash
   nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -f 0 1 2 3 4
   ```
4. Use `nnUNetv2_predict_from_modelfolder` when the model folder is explicit:
   ```bash
   nnUNetv2_predict_from_modelfolder -i INPUT_FOLDER -o OUTPUT_FOLDER -m MODEL_FOLDER -f 0 1 2 3 4
   ```
5. Add `--save_probabilities` when predictions will be ensembled; run `nnUNetv2_ensemble`, then apply postprocessing if a `postprocessing.pkl` was selected.
6. Evaluate predictions with `nnUNetv2_evaluate_folder` when `dataset.json` and `plans.json` are available, or `nnUNetv2_evaluate_simple` for label-list evaluation.

## Bundled References

- `references/cli-reference.md`: exact command routes, flags, defaults, and entry-point distinctions.
- `references/inference-and-evaluation.md`: workflows for prediction, cascades, ensembling, postprocessing, evaluation, best-configuration selection, and Python API use.
- `references/model-sharing.md`: export/import/download commands and custom-trainer portability rules.
- `references/troubleshooting.md`: failure-mode triage for input names, checkpoints, model folders, probabilities, postprocessing metadata, split jobs, devices, and custom trainers.

## Bundled Helper

`check_inference_inputs.py` validates input-folder case/channel naming against `dataset.json` without loading images or importing nnU-Net. It accepts either a `dataset.json` path or a model/results folder containing `dataset.json`.
