---
name: conversion
description: "Plan and safely inspect cross-framework model conversions without
  loading models, downloading artifacts, or running conversion code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Conversion planning

Use this sub-skill when a task needs a framework direction, checkpoint contract,
conversion flag review, or a no-side-effect argument check for this repository's
`convert_models.py`. The source code in this snapshot dispatches only the edges
listed in [the direction matrix](references/direction-matrix.md). Framework
labels are lower-case and exact: `gluon`, `mxnet`, `pytorch`, `chainer`,
`keras`, `tensorflow` (legacy TF1), `tf2` (TF2/Keras), and `tfl` (TFLite
destination only).

This is a planning and validation route. It does not load a model, install a
backend, download weights, or execute conversion code. Route model construction
and checkpoint loading to the model-inference sub-skill, and route backend
installation or compatibility diagnosis to the framework-compatibility
sub-skill. The conversion script imports `cvutil` and other backends before it
can do useful work, so do not use it as a dry-run parser.

## Safe route

1. Read [the direction matrix](references/direction-matrix.md). Treat an absent
   edge as unsupported by this CLI; do not reverse the flags or compose two
   conversions implicitly.
2. From this sub-skill directory, inspect the CLI contract without repository
   imports:

   ```bash
   python3 scripts/inspect_conversion_args.py --list
   ```

   The bundled inspector is standard-library only. It reports the exact
   dispatch function for each edge, required identity/checkpoint flags, and the
   inspector-only policies.
3. Validate a concrete plan before running anything. Supply local source and
   destination paths when available; this checks required arguments, direction,
   positive class/channel counts, model type, path collision, and policy gates:

   ```bash
   python3 scripts/inspect_conversion_args.py \
     --src-fwk gluon --dst-fwk tf2 \
     --src-model resnet18 --dst-model resnet18 \
     --src-params ./resnet18.params --dst-params ./resnet18.tf2.h5
   ```

   Add `--check-files` only when a filesystem-presence check is wanted. It does
   not open a checkpoint. `--cpu-only`, `--entrypoint`, and `--output-dir` are inspector policy
   controls, not flags accepted by `convert_models.py`.
4. Only after a valid plan, use the exact flags in the matrix. Preserve model
   identity, class count, input channel count, and checkpoint provenance. The
   conversion functions assert parameter counts, names, and shapes (with
   documented special cases); the inspector cannot prove those conditions.
5. Validate the converted model through the model-inference route. Do not use
   `prep_model.py` as an argument check: it requires a local Gluon `--resume`
   file and sibling `train.log`, evaluates four publication targets, and writes
   a `_result` directory plus metadata.

## Hard gates

- `tensorflow` is the legacy TensorFlow 1.x graph/session path. `tf2` is the
  TensorFlow 2.x/Keras path. Never exchange these labels. `tfl` is only the
  destination of the TF2-to-TensorFlow-Lite branch.
- The CLI parser itself does not restrict `--model-type`, but destination TF2
  code uses exactly `image` for its image branch and treats every other string
  as the audio branch. The inspector accepts only the documented `image` or
  `audio` values to prevent accidental selection of that fallback.
- `--load-ignore-extra` and `--remove-module` are parsed globally.
  `--load-ignore-extra` is meaningful for Gluon and PyTorch sources: Gluon
  passes it to `load_parameters(ignore_extra=...)`, while PyTorch filters extra
  stored keys. `--remove-module` is meaningful only for a PyTorch source; its
  branch is used only when `load-ignore-extra` is false and handles a
  DataParallel `module.` wrapper. Neither flag repairs shape or architecture
  mismatches.
- A CPU-only `gluon -> pytorch` plan is blocked/unverified by policy. The
  focused Gluon/PyTorch tests explicitly use `mx.gpu(0)` and `.cuda()`; the
  tests do not prove CPU behavior. The main CLI initializes `use_cuda=False`,
  but that implementation detail is not CPU verification.
- The `convert_models.py` `tf2 -> tfl` branch calls TF2 `prepare_model` with
  `use_pretrained=True` and an empty weight path; it does not consume a local
  `--src-params` file, and its `--dst-model` is not used for model
  construction. For no-network local work, use a separately prepared
  local-input TF2-to-TFLite wrapper with its `--input` weight path. That
  wrapper should write `<output-dir>/<model>.tflite` only when the directory
  already exists, then allocate a TFLite interpreter and compare a
  random-input result. This sub-skill's inspector only validates the direction
  and does not perform export.
- The local TF2-to-TFLite example declares `--input-shape` as one `int` with
  a tuple default. Its default is `(1, 640, 480, 3)`, but a custom multi-value shape is not supported
  by this snapshot's parser: one custom integer later fails during slicing and
  four shell integers are rejected by `argparse`. Treat custom shape requests
  as blocked/unverified unless separately wrapped and reviewed.
- Do not run native conversion tests, long training, weight or dataset
  downloads, or backend installation as part of this planning route.

For exact input/output contracts and failure recovery, use
[troubleshooting](references/troubleshooting.md).
