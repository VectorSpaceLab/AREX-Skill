---
name: inference-and-demo
description: "Routes BackgroundMattingV2 image, video, webcam, and throughput
  demo workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# inference-and-demo

Use this sub-skill when the task is about running BackgroundMattingV2 demos or
understanding the inference-time model path.

## Typical triggers

- image matting on a directory of source/background images
- video matting on a source video and a background image or video
- webcam matting, background capture, or GUI interaction
- throughput or speed testing on PyTorch or TorchScript
- choosing `mattingbase` vs `mattingrefine`
- choosing `resnet101`, `resnet50`, or `mobilenetv2`
- using `cpu` vs `cuda`
- deciding when `preprocess-alignment` is helpful

## Read first

- `references/workflows.md` for concrete demo recipes and option meaning.
- `references/troubleshooting.md` for missing checkpoints, shape mismatch,
  alignment, webcam, and output-overwrite issues.
- `scripts/smoke_forward.py` for the safe tiny forward smoke.
- `scripts/run_inference_images.py` and `scripts/run_inference_video.py` for
  dry-run or execute wrappers around the checkout's demo CLIs.

## What this sub-skill owns

- model selection and inference-time configuration
- input pairing and alignment behavior
- output types `com`, `pha`, `fgr`, `err`, and `ref`
- small smoke tests that prove the model path works without checkpoints
- guidance for the webcam demo, while acknowledging its hardware and GUI needs

## What it does not own

- TorchScript or ONNX conversion details; use `export-and-backends`.
- Dataset layout and training setup; use `training`.
- Octave/MATLAB benchmark notes; those stay with `training` references.

## Recommended first checks

1. Run `scripts/smoke_forward.py` with a tiny resolution on CPU or CUDA.
2. If you only want to inspect the exact source CLI, use the dry-run wrappers.
3. Move to the native CLI only when you have a real checkpoint and matching
   source/background inputs.

## Cross-links

- `../export-and-backends/SKILL.md`
- `../training/SKILL.md`
- `../../references/backend-compatibility.md`
