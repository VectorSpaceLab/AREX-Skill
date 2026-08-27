---
name: audio-diffusion-pytorch
description: "Use audio-diffusion-pytorch for PyTorch waveform diffusion
  generators, text-conditioned audio generation, inpainting, upsampling,
  vocoding, and diffusion autoencoding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# audio-diffusion-pytorch

Use this repo skill when a task involves the `audio-diffusion-pytorch` package or asks for PyTorch audio diffusion model setup, waveform generation, diffusion upsampling, mel vocoding, inpainting, or audio autoencoding.

This package provides building blocks and wrappers; it does **not** ship pretrained weights, ready-to-run checkpoints, or guaranteed Moûsai paper configs. Treat examples as model-construction and shape recipes unless the user supplies weights, data, or a training plan.

## Install and quick checks

Install the public package:

```bash
pip install audio-diffusion-pytorch
```

Minimal import check:

```bash
python - <<'PY'
from importlib.metadata import version
import audio_diffusion_pytorch
print(version("audio-diffusion-pytorch"))
print("import ok")
PY
```

Optional dependencies:

- Text conditioning uses the default `a-unet` T5 embedder and requires `transformers`. First use may consult Hugging Face cache or network.
- README-style autoencoder examples may use `audio_encoders_pytorch` and `auraloss`, but the core `DiffusionAE` wrapper can also work with a local encoder object.
- CUDA is optional for this package. CPU is enough for tiny smoke checks; use a CUDA-capable PyTorch install only when the user wants GPU execution.

Run `scripts/check_install.py` to report installed versions, optional modules, and public signatures. Use `--check-cuda` only when you want a tiny CUDA allocation.

## Route map

- Use `sub-skills/generation/SKILL.md` for `DiffusionModel`, `UNetV0`, `VDiffusion`, `VSampler`, text-conditioned generation, `VInpainter`, schedules, distributions, and expert `DiffusionAR` notes.
- Use `sub-skills/conditioning/SKILL.md` for `DiffusionUpsampler`, `DiffusionVocoder`, `DiffusionAE`, `EncoderBase`, `AdapterBase`, mel spectrogram conditioning, and transform plugins.
- Use `references/troubleshooting.md` for install/import issues, optional dependencies, backend questions, no-pretrained-weights expectations, and cross-cutting shape gotchas.
- Use `references/repo-provenance.md` before deciding whether this skill is current for a checkout or should be refreshed.

## Common decisions

1. Identify the workflow family first:
   - new waveform generation, text prompts, sampler errors, or masks → `generation`;
   - lower-rate waveform conditioning, mel spectrograms, latents, encoders, adapters, or custom losses → `conditioning`.
2. Keep smoke tests tiny: use channel counts and lengths from the bundled scripts before scaling to README-sized tensors.
3. Set `resnet_groups=1` for tiny channels, or use channel widths divisible by the default `resnet_groups=8`.
4. Keep tensors on one device. Move the model and all inputs to CUDA only after CPU shape checks pass.
5. Do not promise audio quality from random weights. Sampling APIs validate shape and execution, not trained generation quality.

## Avoid this skill when

- The user wants a pretrained audio diffusion checkpoint, dataset download, or benchmark reproduction and has not supplied the missing assets.
- The task is about non-PyTorch audio libraries, ASR/TTS pipelines unrelated to diffusion/vocoding, or image diffusion.
- The user is editing this repository's release workflow rather than using the package APIs.

## Maintenance note

This skill is self-contained for operating use. If a future checkout changes package metadata, public constructors, README workflows, or source roots, run `refresh-repo-skill` instead of patching this skill ad hoc.
