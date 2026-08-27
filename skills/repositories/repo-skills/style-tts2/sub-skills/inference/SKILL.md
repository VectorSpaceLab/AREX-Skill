---
name: inference
description: "Pretrained StyleTTS2 inference, asset checks, phonemizer
  readiness, and long-form synthesis troubleshooting for LJSpeech and LibriTTS."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

Use this sub-skill for pretrained StyleTTS2 demos and troubleshooting only.
It covers the LJSpeech single-speaker path, the LibriTTS multi-speaker path,
reference-audio style extraction, diffusion/style controls, and safe asset
checks.

## Route elsewhere

- Training or fine-tuning -> the `training` sub-skill.
- Data-list prep or config edits -> the `data-and-config` sub-skill.

## Start here

Run [scripts/check_inference_assets.py](scripts/check_inference_assets.py) before trying to synthesize. It inspects expected checkpoints, bundled helper assets, optional phonemizer/espeak readiness, and LibriTTS reference-audio availability without downloading or generating audio.

## Bundled references

- [references/inference-workflows.md](references/inference-workflows.md) for distilled LJSpeech and LibriTTS synthesis procedures and control parameters.
- [references/model-assets.md](references/model-assets.md) for required checkpoints, reference audio, and public download locations.
- [references/troubleshooting.md](references/troubleshooting.md) for phonemizer, asset, backend, and voice-permission issues.

## Cautions

- Treat generated speech as synthesized unless you have permission and license
to use the voice.
- The README notes a GPL-licensed fork and an MIT-licensed PyPI package as
external alternatives, but they are not this repository's core workflow.
- Older GPUs can produce high-pitched background noise; prefer a newer CUDA GPU
or CPU inference if you hit that issue.

## Output contract

The notebook workflows produce 24 kHz waveforms, usually returned as NumPy
arrays that can be played with `IPython.display.Audio`.
