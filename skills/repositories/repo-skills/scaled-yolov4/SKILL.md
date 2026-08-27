---
name: scaled-yolov4
description: "Repo-specific guidance for ScaledYOLOv4 data preparation,
  training, evaluation, inference, and export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# ScaledYOLOv4

ScaledYOLOv4 is a YOLOv4-family object-detection checkout centered on five user-facing workflows: dataset preparation, training, evaluation, inference, and export.

## Start here

Use this root skill as the router, then jump to the sub-skill that owns the workflow you need:

- `sub-skills/data-preparation/` for dataset YAMLs, label layout, augmentation, anchors, caching, and dataset sanity checks.
- `sub-skills/training/` for training, fine-tuning, distributed launch, checkpoints, tensorboard logging, and resume flows.
- `sub-skills/evaluation/` for validation, COCO-style metrics, `study` sweeps, and result interpretation.
- `sub-skills/inference/` for image, video, webcam, and stream detection workflows.
- `sub-skills/export/` for TorchScript, ONNX, and CoreML export planning.

## What matters globally

- `models/common.py` imports `mish_cuda.MishCuda` as the default Mish activation. Full model import and forward checks therefore need a CUDA-capable inspection environment with that extension available.
- The skill also bundles a self-contained `runtime/` mirror with the concrete `detect.py`, `test.py`, `train.py`, `models/`, `utils/`, and YAML/config files that the helper scripts run against.
- `models/yolo.py` builds the model from YAML, computes strides from a synthetic forward pass, and initializes anchors and biases.
- `utils/datasets.py` and `utils/general.py` contain most of the shared data, augmentation, metric, anchor, and plotting helpers used across the repo.
- The repository is script-first rather than package-first, so the bundled helpers under `scripts/`, the sub-skill `scripts/` folders, and the packaged `runtime/` mirror are the preferred entry points for future agents.

## Bundled helpers

- `scripts/check_runtime_bundle.py` verifies that the bundled `runtime/` mirror contains the required entrypoints, modules, and YAML configs.
- `scripts/check_cli.py` checks the public parser surfaces against the bundled `runtime/` mirror without starting long workflows.
- `scripts/check_model_forward.py` builds a YAML model from the bundled `runtime/` mirror and runs a tiny synthetic forward pass under `torch.no_grad()`.
- `scripts/run_runtime_entrypoint.py` executes concrete bundled runtime entrypoints (`detect`, `test`, `train`, `export`, or `yolo`) with the correct working directory and `PYTHONPATH`; use `--dry-run` before long jobs.

## Shared references

Read these when you need a cross-cutting view before choosing a sub-skill:

- `references/model-overview.md` for model families, YAML structure, the detect head, and the `mish_cuda` dependency.
- `references/runtime-bundle.md` for the bundled executable source mirror and the configs the helpers use.
- `references/data-layout.md` for dataset YAMLs, image/label layout, and the supported data utilities.
- `references/cli-reference.md` for the main workflow options and the bundled helper scripts.
- `references/troubleshooting.md` for the most common repository-wide failures and recovery steps.
- `references/repo-provenance.md` for the source snapshot this skill was distilled from.
- `references/repo-routing-metadata.json` for the router metadata used by managed repo-skill import.

## Practical routing rules

If the request mentions multiple workflows, route by the primary user intent first:

- Dataset format, label cleanup, anchor planning, or cache issues → `data-preparation`.
- Epochs, resume, DDP, logging, checkpoints, or training loss behavior → `training`.
- mAP, AP, COCO JSON, study sweeps, or standalone validation → `evaluation`.
- Files, folders, webcams, RTSP, or rendered detections → `inference`.
- TorchScript, ONNX, CoreML, or deployment conversion → `export`.

If the request is only about model architecture or imported modules, use `references/model-overview.md` before choosing a workflow. If it is only about parser shape or smoke validation, use the bundled helpers first.

## Environment expectation

A CPU-only environment is enough for reading the skill, validating dataset paths, and checking CLI help. A CUDA-capable environment is required to prove the model stack imports and runs a forward pass because of the Mish CUDA extension.

## Self-contained usage

Everything a future agent needs should come from this skill tree, not the original checkout layout. Use the bundled runtime mirror, references, and scripts for the concrete workflows. Avoid reaching back into source files when the same answer is already captured here.
