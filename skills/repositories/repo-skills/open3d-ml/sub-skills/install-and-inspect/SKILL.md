---
name: install-and-inspect
description: "Guides Open3D-ML installation, import smoke checks, backend
  compatibility, and common startup failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Install and Inspect

Use this sub-skill when you need to get Open3D-ML importable, confirm the
installed backend surface, or diagnose an initialization problem before you
start dataset, training, or visualization work.

## What this sub-skill covers

- Public installation commands for Open3D, PyTorch, and related runtime pieces.
- Source-checkout integration through `OPEN3D_ML_ROOT` when using an external
  Open3D wheel with the Open3D-ML source tree.
- Import/version/backend smoke checks for `open3d`, `open3d.ml`, and
  `open3d.ml.torch`.
- Optional backend notes for TensorFlow, CUDA, GUI, TensorBoard, and OpenVINO.
- Common startup failures such as version mismatch, missing namespace wiring,
  NumPy/compiled-extension incompatibility, and backend-specific import gaps.

## When to route here

- "How do I install Open3D-ML?"
- "Why does `open3d.ml.torch` fail to import?"
- "Is my Open3D wheel compatible with this torch version?"
- "How do I check whether CUDA/TensorFlow/OpenVINO is available?"
- "Why does a local checkout need `OPEN3D_ML_ROOT`?"

## Use the bundled helper

Run `scripts/check_open3d_ml.py` when you want a fast, safe smoke check that
prints a machine-readable summary of the installed distribution versions,
backend importability, and optional config loading.

## Reading order

1. Read `references/install-and-backends.md` for install choices and the
   verified backend matrix.
2. Read `references/troubleshooting.md` when the import smoke check fails or a
   backend is unavailable.
3. Use `scripts/check_open3d_ml.py` for a quick status report.

## Boundary notes

Include:
- Package installation and editable/source integration.
- Import smoke checks and backend availability.
- Safe explanation of `OPEN3D_ML_ROOT`.

Exclude:
- Dataset layout validation; use `datasets-and-preprocessing`.
- Training command construction and config selection; use
  `training-and-pipelines`.
- Visualization fixtures or TensorBoard summaries; use
  `visualization-and-extensions`.

## Minimal workflow

1. Install Open3D and a compatible PyTorch wheel.
2. Export `OPEN3D_ML_ROOT` only when using a source checkout with an external
   Open3D wheel.
3. Run `scripts/check_open3d_ml.py --framework torch`.
4. If the check fails, follow the troubleshooting reference before proceeding.

## Good handoff signals

A future agent should be able to answer these from this sub-skill alone:

- Which packages must be present for a CPU PyTorch smoke check.
- How to tell whether the installed Open3D wheel exposes PyTorch ops.
- What to do when TensorFlow or OpenVINO is optional but unavailable.
- How to recover from torch/Open3D or NumPy/extension mismatch errors.
