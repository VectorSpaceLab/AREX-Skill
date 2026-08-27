---
name: gfpgan
description: "Use GFPGAN for face-restoration inference, model-version
  selection, training/data preparation, checkpoint conversion, and package
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GFPGAN Repo Skill

Use this repo skill when a user asks about `gfpgan`, GFPGAN face restoration, blind real-world face enhancement, GFPGAN model versions, the `GFPGANer` helper API, the `inference_gfpgan.py` workflow, or GFPGAN training and FFHQ degradation data preparation.

## Choose A Route

- `sub-skills/inference/`: restore faces from images or folders, choose GFPGAN versions (`1`, `1.2`, `1.3`, `1.4`, `RestoreFormer`), use aligned crop mode, call the `GFPGANer` API, interpret output folders, and debug checkpoint/device/image failures.
- `sub-skills/training/`: prepare FFHQ-style data, configure `FFHQDegradationDataset`, run BasicSR-backed GFPGAN training, inspect `GFPGANModel`, generate landmark files, and convert bilinear/original checkpoints into clean checkpoints.

## Quick Install Check

GFPGAN is a PyTorch package named `gfpgan`. A typical runtime environment needs PyTorch, TorchVision, BasicSR, facexlib, OpenCV, LMDB, NumPy, PyYAML, SciPy, and tqdm. For image restoration only, install GFPGAN and its base dependencies first; install `realesrgan` only when background upsampling is required.

```bash
python scripts/check_env.py
```

Read `references/installation.md` before changing PyTorch/CUDA wheels, installing optional Real-ESRGAN, or using the original paper model that depends on BasicSR extension/JIT behavior.

## Core Facts

- Public package version captured for this skill: `1.3.8`.
- The main high-level inference API is `gfpgan.utils.GFPGANer(model_path, upscale=2, arch='clean', channel_multiplier=2, bg_upsampler=None, device=None)`.
- `GFPGANer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True, weight=0.5)` returns cropped faces, restored faces, and optionally the pasted-back restored image.
- Clean models (`1.2`, `1.3`, `1.4`) do not require custom CUDA extensions; the original paper model (`1`) uses the original architecture and may need BasicSR JIT/extension setup.
- Training is BasicSR-backed, data/checkpoint heavy, and normally GPU/multi-GPU oriented. Do not present full training as a cheap smoke test.

## Shared References

- `references/installation.md`: install variants, dependency roles, CUDA/CPU notes, optional Real-ESRGAN, and original-model extension guidance.
- `references/troubleshooting.md`: cross-cutting package import, checkpoint, CUDA, OpenCV, BasicSR, and optional dependency failures.
- `references/repo-provenance.md`: source commit, dirty-state baseline, package version, and evidence paths used to generate this skill.
- `references/repo-routing-metadata.json`: structured DisCo router metadata used during managed repo-skill import.

## Shared Scripts

- `scripts/check_env.py`: verifies importability, important signatures, package metadata, CUDA visibility, and optional dependency availability without downloading model weights.

## Routing Notes

- If the user wants a restored image, output-folder explanation, checkpoint choice, or `GFPGANer.enhance`, start with `sub-skills/inference/`.
- If the user wants to train, fine-tune, convert checkpoints, fix an FFHQ data layout, or understand `options/train_gfpgan_v1*.yml`, start with `sub-skills/training/`.
- If the user asks for Cog/Replicate/Hugging Face demo deployment, treat it as an external deployment adaptation: use inference knowledge for the model call, but do not run service-specific scripts unless the user explicitly requests that environment.
