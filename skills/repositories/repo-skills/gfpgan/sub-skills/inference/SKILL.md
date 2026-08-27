---
name: inference
description: "Use GFPGAN for face-restoration inference, model-version
  selection, aligned crop handling, GFPGANer API calls, and inference
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GFPGAN Inference

Use this sub-skill when a user wants to restore faces from a photo, folder, aligned crop, or application pipeline with GFPGAN.

## Use This For

- Running GFPGAN on one image or a directory of images.
- Choosing between versions `1`, `1.2`, `1.3`, `1.4`, and `RestoreFormer`.
- Deciding whether to use `--aligned`, `--only-center-face`, `--suffix`, `--ext`, `--weight`, or background upsampling.
- Calling `gfpgan.GFPGANer` from Python code.
- Explaining output folders such as cropped faces, restored faces, comparison images, and pasted-back restored images.
- Debugging missing checkpoints, missing optional Real-ESRGAN, no face detections, CPU/GPU surprises, OpenCV image failures, or output naming confusion.

## Route Elsewhere

- Training configs, FFHQ data, dataset degradation, landmark files, and checkpoint conversion: use `../training/`.
- Package-wide install/CUDA import problems: start with `../../references/installation.md` and `../../references/troubleshooting.md`.
- Cog/Replicate/Gradio deployment: use this sub-skill for the GFPGAN model call, but treat deployment-specific packaging as a separate application task.

## Quick Start

Prefer the bundled helper when you need a safe, explicit inference run that does not auto-download weights by default:

```bash
python sub-skills/inference/scripts/run_inference.py \
  --input /path/to/input.jpg \
  --output outputs/gfpgan \
  --model-path /path/to/GFPGANv1.4.pth \
  --version 1.4 \
  --upscale 2 \
  --no-bg-upsampler
```

For already aligned face crops:

```bash
python sub-skills/inference/scripts/run_inference.py \
  --input /path/to/aligned-crops \
  --output outputs/gfpgan-crops \
  --model-path /path/to/GFPGANv1.3.pth \
  --version 1.3 \
  --aligned \
  --ext png
```

## References

- `references/workflows.md`: end-to-end CLI and API recipes, output layout, and validation steps.
- `references/cli-reference.md`: verified command-line flags, defaults, and model path behavior.
- `references/model-selection.md`: version/architecture tradeoffs, checkpoint filenames, and background upsampler decisions.
- `references/troubleshooting.md`: inference-specific failures and recovery actions.

## Bundled Scripts

- `scripts/run_inference.py`: safe GFPGAN inference wrapper with explicit checkpoint handling and no network download unless requested.
- `scripts/check_env.py`: inference-focused import/signature/backend check that avoids loading model weights.

## Decision Notes

- Use `version=1.4` or `1.3` for most modern clean inference requests unless the user specifically needs `1.2`, the original paper model `1`, or RestoreFormer.
- Use `--aligned` only when inputs are already aligned face crops; for whole photos, leave it off so GFPGAN detects and pastes faces back.
- Use `--no-bg-upsampler` when the user only needs face restoration or is on CPU. Add Real-ESRGAN only when non-face background upsampling is a real requirement.
- Do not imply that a missing checkpoint can be silently ignored. Tell the user which checkpoint file/version is needed.
