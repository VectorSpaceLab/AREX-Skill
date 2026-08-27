---
name: export
description: "TorchScript, ONNX, and CoreML export planning for ScaledYOLOv4."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Export

Use this sub-skill when the user wants to convert a trained checkpoint into a deployment-friendly format.

## Typical requests

- How do I export to TorchScript or ONNX?
- Can this checkout produce a CoreML model?
- Which optional dependencies are required for export?
- Why does the export path fail even though the checkpoint loads?
- How do I know whether the environment is ready for export before I start?

## What this sub-skill owns

- TorchScript, ONNX, and CoreML export planning.
- Fused-model preparation and dry-run tracing behavior.
- Optional backend checks for `onnx` and `coremltools`.
- Export-specific failure modes and output naming.

## What it does not own

- Dataset preparation and label cleanup → `../data-preparation/`.
- Training and epoch-end checkpoints → `../training/`.
- Standalone validation metrics → `../evaluation/`.
- Image/video/webcam/stream detection → `../inference/`.

## Read before acting

- `../../references/model-overview.md` for the model builder, detect head, and `mish_cuda` dependency.
- `../../references/runtime-bundle.md` for the bundled executable source mirror and configs used by the helper.
- `../../references/cli-reference.md` for the export-related planning inputs.
- `references/export-workflows.md` for the format-specific workflow details.
- `references/troubleshooting.md` for export-specific failures and recovery steps.

## Bundled helper

- `scripts/check_export_env.py` reports whether the optional export backends are available before you start a conversion against the bundled `runtime/` mirror.
- `scripts/run_export.py` runs the concrete bundled `runtime/models/export.py` entrypoint with the correct working directory and `PYTHONPATH`; use `--dry-run` before launching.

## Workflow in practice

1. Confirm that the checkpoint exists and loads in the current environment.
2. Decide which format you actually need.
3. Check whether `onnx` or `coremltools` are installed before assuming those targets are possible.
4. Prefer the simplest export target that satisfies the downstream consumer.
5. Treat conversion failures as backend or compatibility issues until proven otherwise.

## Good signs

- The checkpoint is valid and the model can fuse or trace.
- The optional backend you want is installed.
- The target format matches the downstream toolchain.
- You are not trying to mix incompatible export goals in one run.

## Bad signs

- The environment lacks the optional package for the requested format.
- The checkpoint has not been tested in the installed environment.
- You are attempting CoreML conversion on a machine that cannot support it.
- You are using export to debug a training-quality issue instead of a deployment issue.
