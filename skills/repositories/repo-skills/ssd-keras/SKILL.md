---
name: ssd-keras
description: "Router for SSD300, SSD512, and SSD7 Keras detection workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SSD Keras

This skill routes work on the SSD Keras repository. It covers the SSD300, SSD512, and SSD7 model builders, the custom layers and losses they depend on, the data generator and augmentation stack, training and fine-tuning workflows, and Pascal VOC / MS COCO inference and evaluation.

## Quick compatibility note

Use a Python 3.7 environment with TensorFlow 1.15.x and Keras 2.2.x. The verified baseline also needs protobuf 3.20.x or lower. The codebase is TensorFlow-only; Theano and CNTK are unsupported. Start with `scripts/check_env.py` before deeper work.

## Choose a route

### `data-preparation`
Use this route when the task is about:
- parsing CSV, Pascal VOC XML, COCO JSON, or HDF5 data
- validating boxes, labels, and image sets
- creating batches or augmentation pipelines
- using `DataGenerator`, `BoxFilter`, `ImageValidator`, or `apply_inverse_transforms`

Read:
- `sub-skills/data-preparation/SKILL.md`
- `references/data-formats.md`
- `references/workflows.md`
- `sub-skills/data-preparation/references/troubleshooting.md`

### `training`
Use this route when the task is about:
- building a trainable model
- loading VGG / pretrained SSD weights
- compiling with `SSDLoss`
- wiring `SSDInputEncoder`
- fitting on VOC, custom CSV data, or synthetic fixtures
- adapting weights with `sample_tensors`

Read:
- `sub-skills/training/SKILL.md`
- `references/model-architecture.md`
- `references/workflows.md`
- `sub-skills/training/references/troubleshooting.md`

### `inference-evaluation`
Use this route when the task is about:
- loading a trained model
- decoding predictions
- drawing or interpreting detections
- computing VOC mAP or COCO JSON output
- using `Evaluator`, `decode_detections`, `decode_detections_fast`, or `predict_all_to_json`

Read:
- `sub-skills/inference-evaluation/SKILL.md`
- `references/model-architecture.md`
- `references/workflows.md`
- `sub-skills/inference-evaluation/references/troubleshooting.md`

## Shared references

- `references/model-architecture.md` — constructors, modes, custom layers, encoder/decoder, and box math.
- `references/data-formats.md` — CSV/XML/JSON/HDF5 layouts and generator outputs.
- `references/compatibility.md` — supported Python and dependency baseline.
- `references/runtime-source.md` — bundled runtime module layout used by the smoke scripts.
- `references/troubleshooting.md` — cross-cutting backend, import, and shape mismatches.
- `references/workflows.md` — notebook-derived end-to-end recipes.

## Smoke path

When you only need a fast confidence check, run:
1. `scripts/check_env.py`
2. the smoke script owned by the relevant sub-skill
3. the smallest synthetic case described in that sub-skill's troubleshooting notes

The smoke scripts resolve imports from the bundled `runtime-src/` copy of the Python modules, so they do not rely on an external checkout.

## What this skill does not do

- It does not run or document maintainer release automation.
- It does not expose Theano or CNTK paths.
- It does not depend on the original repository's absolute checkout path.
- It does not require the notebooks to stay available once the skill is loaded.

## Entry-point summary

- Bundled runtime source lives under `runtime-src/` and mirrors the repo's Python package layout.
- Model constructors live under `models/`.
- Loss and encoder utilities live under `keras_loss_function/` and `ssd_encoder_decoder/`.
- Dataset parsing and augmentation live under `data_generator/`.
- Evaluation helpers live under `eval_utils/`.
- Weight sampling utilities live under `misc_utils/`.

If you need an unfamiliar object or function, open the shared reference that matches the workflow before reading the source tree.
