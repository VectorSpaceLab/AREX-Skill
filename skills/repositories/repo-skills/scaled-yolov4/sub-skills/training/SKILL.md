---
name: training
description: "Training, fine-tuning, distributed launch, checkpointing, logging,
  and resume workflows for ScaledYOLOv4."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Training

Use this sub-skill for anything that starts, resumes, or analyzes a training run.

## Typical requests

- How do I train from scratch or fine-tune from a checkpoint?
- Which flags matter for DDP, `sync_bn`, `multi_scale`, or resume?
- Why is the run failing before the first epoch?
- How do I interpret checkpoints, logs, and plotted results?
- What training settings are safe for a new dataset?

## What this sub-skill owns

- The training loop and run configuration.
- Distributed launch, device selection, and resume behavior.
- TensorBoard logging, `results.txt`, and checkpoint outputs.
- Autoanchor checks, class-weight preparation, and epoch-level validation.
- Hyperparameter evolution and post-run plotting behavior.

## What it does not own

- Dataset format and label cleanup → `../data-preparation/`.
- Standalone validation metrics → `../evaluation/`.
- Inference on images or streams → `../inference/`.
- Export to TorchScript, ONNX, or CoreML → `../export/`.

## Read before acting

- `../../references/model-overview.md` for model-building and Mish CUDA expectations.
- `../../references/runtime-bundle.md` for the bundled executable source mirror and configs used by the helper.
- `../../references/data-layout.md` for the dataset and label format that training expects.
- `references/training-workflows.md` for the run structure and important flags.
- `references/troubleshooting.md` for training-specific failures and recovery steps.

## Bundled helper

- `scripts/prepare_training_run.py` validates the key training inputs against the bundled `runtime/` mirror and prints a canonical run plan before you start a long job.
- `scripts/run_training.py` runs the concrete bundled `runtime/train.py` entrypoint with the correct working directory and `PYTHONPATH`; use `--dry-run` before launching.

## Workflow in practice

1. Confirm that the dataset YAML is valid and the labels are normalized.
2. Decide whether the run is scratch training, fine-tuning, or resume.
3. Validate the image size, batch size, device, and distributed settings.
4. Start the long run only after the preflight helper agrees with the plan.
5. Watch the epoch logs, checkpoint outputs, and validation summaries.

## Good signs

- `nc` and `names` are aligned before training begins.
- The image size is stride-compatible.
- The chosen batch size fits the device count and memory budget.
- `results.txt`, `best.pt`, and `last.pt` appear in the expected run directory.

## Bad signs

- The run fails before the model is built.
- `--cfg` and `--weights` are both missing.
- The batch size is not divisible by the world size in DDP mode.
- The dataset labels or class count are inconsistent.
