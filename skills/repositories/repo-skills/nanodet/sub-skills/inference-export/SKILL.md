---
name: "inference-export"
description: "Routes NanoDet image/video/webcam inference, checkpoint export,
  deploy-conversion, and FLOPs workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# inference-export

Use this sub-skill when you need to run a NanoDet demo, export a checkpoint, or prepare a model for deployment backends.

## Use this route for

- Image, video, or webcam inference.
- Exporting a checkpoint to ONNX or TorchScript.
- Preparing RepVGG models for deploy mode before export.
- Inspecting FLOPs or model-complexity behavior.
- Reading deployment notes for ncnn, MNN, OpenVINO, or LibTorch.

## Do not use this route for

- Training, validation, or checkpoint resume logic. Use `training` instead.
- Dataset schema / config validation. Use `dataset-config` instead.

## Read first

- `references/workflows.md` for inference and export flow details.
- `references/deployment.md` for backend-specific deployment notes.
- `references/troubleshooting.md` for export and demo failures.
- `../../references/api-reference.md` for verified model / utility signatures.

## Skill-owned scripts

- `scripts/demo.py` — run image, video, or webcam inference with explicit device selection.
- `scripts/export_onnx.py` — export a checkpoint to ONNX and simplify it when possible.
- `scripts/export_torchscript.py` — export a checkpoint to TorchScript.
- `scripts/flops.py` — print FLOPs when the optional helper dependency is available.

## Typical workflow

1. Validate the config with `dataset-config`.
2. Make sure the checkpoint is compatible with the selected model family.
3. Run the skill-owned demo or export script.
4. For deployment backends, read the distilled deployment notes before switching toolchains.

## Cross-links

- If you need to convert an old `.pth` checkpoint before export, use `training` first.
- If you only need to inspect a config or dataset layout, switch to `dataset-config`.
