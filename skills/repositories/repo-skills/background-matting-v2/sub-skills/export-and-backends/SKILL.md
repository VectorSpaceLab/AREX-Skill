---
name: export-and-backends
description: "Routes BackgroundMattingV2 TorchScript and ONNX export workflows
  and backend compatibility checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# export-and-backends

Use this sub-skill when the task is about converting BackgroundMattingV2 models
or deciding which runtime/backend path is safe.

## Typical triggers

- TorchScript export
- ONNX export
- choosing `roi_align`, `gather`, `unfold`, `scatter_nd`, or
  `scatter_element`
- checking whether a scripted or exported model still loads
- deciding how to validate an export without a real checkpoint
- comparing PyTorch, TorchScript, and ONNX Runtime behavior

## Read first

- `references/workflows.md` for export recipes and compatibility choices.
- `references/troubleshooting.md` for export and runtime failures.
- `scripts/check_export_support.py` for the safe dummy-model smoke.
- `scripts/run_export_torchscript.py` and `scripts/run_export_onnx.py` for
  dry-run or execute wrappers around the checkout's exporters.

## What this sub-skill owns

- TorchScript export intent and attribute-hoisting behavior
- ONNX export intent, dynamic axes, and patch-method compatibility choices
- conversion validation without checkpoints, including the `onnx` exporter dependency and ONNX Runtime load step
- exporter-specific failure handling and runtime compatibility notes

## What it does not own

- ordinary image/video/webcam inference; use `inference-and-demo`
- dataset layout or training; use `training`

## Recommended first checks

1. Run `scripts/check_export_support.py` to verify scripting and optional ONNX
   runtime loading on a tiny random model.
2. Use the dry-run wrappers if you only need the exact export command shape.
3. Only run the native export CLI with a real checkpoint when you actually need
   a converted artifact.

## Cross-links

- `../inference-and-demo/SKILL.md`
- `../training/SKILL.md`
- `../../references/backend-compatibility.md`
