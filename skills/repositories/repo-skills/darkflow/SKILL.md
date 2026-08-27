---
name: darkflow
description: "Routes Darkflow object-detection, training, and export workflows
  for the legacy YOLO package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Darkflow

Darkflow is the legacy TensorFlow 1.x YOLO package exposed by the `flow` CLI and the `darkflow.net.build.TFNet` API.

Use this skill when the user wants to:

- run detections on images, folders, videos, or a webcam
- read JSON predictions or call `return_predict()` from Python
- export a frozen `.pb` / `.meta` pair or load one for inference
- train or fine-tune a YOLO model on Pascal VOC style annotations
- adapt Darkflow-compatible config files and labels for a custom dataset

## Start here

1. If the package is not installed yet, read `references/installation.md`.
2. Run `scripts/check_install.py` to confirm the import stack before deeper work.
3. Use `sub-skills/inference/SKILL.md` for prediction, demo, JSON, and protobuf export/import.
4. Use `sub-skills/training/SKILL.md` for dataset prep, labels, training, and checkpoints.

## Verified install shape

The verified inspection path used a Python 3.6 environment with:

- `tensorflow==1.4.1`
- `opencv-python`
- `numpy`
- `requests`
- `Cython<3`
- `pytest` and `pytest-cov` for test-backed validation

If editable install fails with a Cython compile error, see `references/troubleshooting.md`. The legacy build needs a pre-3.0 Cython release.

## Quick smoke checks

- `python scripts/check_install.py`
- `flow --help` or `python scripts/flow.py --help`
- `python -m pip check`

## Read these references when needed

- `references/cli-reference.md` for flags, defaults, and command patterns
- `references/api-reference.md` for `TFNet` and `argHandler` signatures
- `references/model-overview.md` for bundled config families and label rules
- `references/troubleshooting.md` for install, import, build, and runtime failures
- `references/repo-provenance.md` before refreshing or comparing this skill to a new checkout

## Route map

- **Inference / export**: image folders, JSON output, camera or video demo, Python predictions, `.pb` export, or `.pb` / `.meta` loading.
- **Training / custom data**: `--train`, Pascal VOC XML annotations, `labels.txt`, `--dataset`, `--annotation`, checkpointing, or custom config editing.

If a request spans both routes, begin with training for dataset/config preparation and finish with inference for prediction or export.
