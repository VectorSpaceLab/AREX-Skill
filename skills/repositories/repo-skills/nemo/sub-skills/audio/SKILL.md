---
name: audio
description: "Use for NeMo Speech audio-to-audio enhancement, restoration,
  separation, denoising, beamforming, generation, Lhotse audio manifests,
  evaluation, augmentation saving, multi-channel handling, and audio
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Audio

Use this sub-skill for NeMo Speech audio-to-audio work: enhancement, restoration, denoising, source separation, beamforming, background-noise removal, predictive/generative audio models, audio model processing APIs, Lhotse audio manifests, objective evaluation, online augmentation export, and multi-channel audio handling.

Route classic speech transcription, timestamps, ASR decoding, and ASR fine-tuning to `../asr/SKILL.md`. Route text-to-speech waveform synthesis to the TTS sub-skill when available. Route generic manifest sharding, tokenizer building, and dataset conversion utilities to the data-tools sub-skill when available.

## Start Here

1. Read `references/workflows.md` for audio processing, evaluation, training, fine-tuning, Lhotse, augmentation-saving, and multi-channel workflows.
2. Read `references/api-reference.md` before using `AudioToAudioModel`, model subclasses, dataset factories, Lhotse conversion helpers, metrics, losses, transforms, masking, or Maxine BNR classes.
3. Read `references/configuration.md` before editing Hydra YAML, dataset manifests, Lhotse CutSet/Shar settings, model-family configs, sampler overrides, metrics, or output paths.
4. Read `references/troubleshooting.md` when imports, optional dependencies, CUDA/backends, manifest schemas, Hydra overrides, model loading, processing, evaluation, Lhotse, augmentation, or multi-channel workflows fail.

## Safe Bundled Tools

- `scripts/check_audio_manifest.py` validates audio-to-audio JSONL manifests without importing NeMo, downloading models, opening audio contents, training, or writing outputs.
- Run it before long processing, training, or evaluation jobs: `python scripts/check_audio_manifest.py data.jsonl --input-key noisy_filepath --target-key clean_filepath --check-files --output-dir outputs/enhanced --output-manifest outputs/enhanced_manifest.json`.
- Use `--require-target` for training/evaluation manifests and omit it for inference-only manifests where target audio is intentionally absent.

## Evidence Base

This sub-skill distills repository evidence from `docs/source/audio/intro.rst`, `docs/source/audio/models.rst`, `docs/source/audio/datasets.rst`, `docs/source/audio/configs.rst`, `docs/source/audio/api.rst`, `examples/audio/*.py`, `examples/audio/conf/*.yaml`, `nemo/collections/audio/models/*.py`, `nemo/collections/audio/data/**`, and `tests/collections/audio/**`. Runtime guidance is self-contained; do not require future agents to reopen those source files or run the original example scripts.
