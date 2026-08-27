---
name: evaluation
description: "Standalone validation, COCO metrics, study sweeps, and result
  interpretation for ScaledYOLOv4."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Evaluation

Use this sub-skill when the user wants to validate a checkpoint, score a split, or interpret the metric output of this repository.

## Typical requests

- How do I run standalone validation on a checkpoint?
- What does the AP / mAP output mean?
- How do I use the COCO JSON path or the `study` mode?
- Why is validation failing even though the model loads?
- How do I compare multiple weight files?

## What this sub-skill owns

- The standalone evaluation entry point and its options.
- COCO-style metrics, per-class AP, and speed reporting.
- JSON export for COCO evaluation.
- The `study` sweep that measures different image sizes.
- Evaluation-time plotting of predictions and ground truth.

## What it does not own

- Dataset preparation and label cleanup → `../data-preparation/`.
- Training-time epoch evaluation and checkpoints → `../training/`.
- Image/video/webcam/stream inference → `../inference/`.
- TorchScript, ONNX, or CoreML export → `../export/`.

## Read before acting

- `../../references/model-overview.md` for model loading and stride behavior.
- `../../references/runtime-bundle.md` for the bundled executable source mirror and configs used by the helper.
- `../../references/data-layout.md` for the dataset and label conventions used by evaluation.
- `references/evaluation-workflows.md` for the main run patterns and metrics.
- `references/troubleshooting.md` for validation-specific failures and recovery steps.

## Bundled helper

- `scripts/prepare_evaluation_run.py` validates checkpoint and split inputs against the bundled `runtime/` mirror before you start a validation or study job.
- `scripts/run_evaluation.py` runs the concrete bundled `runtime/test.py` entrypoint with the correct working directory and `PYTHONPATH`; use `--dry-run` before launching.

## Workflow in practice

1. Decide whether you want `val`, `test`, or `study`.
2. Confirm that the weights file and dataset YAML both resolve.
3. Decide whether you need JSON export, text output, or augmented inference.
4. Run the preflight helper and review the metric expectations.
5. Compare the reported AP values against the baseline you care about.

## Good signs

- The checkpoint loads and the image size is compatible with the model stride.
- The dataset split resolves to real images.
- `save_json` is only enabled when you need COCO output.
- Per-class metrics are interpretable and the speed report is sane.

## Bad signs

- `pycocotools` is missing when you asked for COCO JSON.
- The checkpoint path or dataset split path does not exist.
- The evaluation split is malformed or empty.
- You are trying to use evaluation output as a substitute for fixing data-label problems.
