# Package Overview

## Purpose

Read this when you need the shortest accurate mental model of the Coqui TTS package before choosing a sub-skill.

## Snapshot used for this skill

- Distribution: `TTS`
- Version: `0.22.0`
- Supported Python: `>=3.9, <3.12`
- Installed console entry points: `tts`, `tts-server`
- Core runtime families in this snapshot:
  - Python TTS inference API and released-model registry
  - CLI and local demo server
  - TTS training/config/data preparation
  - Vocoder/audio preprocessing helpers
  - FreeVC voice conversion

## Core runtime objects

- `TTS.api.TTS`: high-level Python interface for released models and custom checkpoints.
- `TTS.utils.manage.ModelManager`: registry/list/query/download helper for released TTS, vocoder, and voice-conversion models.
- `TTS.utils.synthesizer.Synthesizer`: lower-level inference/runtime engine for TTS, vocoder, encoder, and voice-conversion checkpoints.
- `TTS.config.load_config` / `register_config`: Coqpit-based config loading and model config registration.
- `TTS.tts.datasets.load_tts_samples`: dataset loading entry point used by training and helper scripts.
- `TTS.utils.audio.AudioProcessor`: audio feature extraction and I/O helper for training and vocoder workflows.

## Model families

- **TTS models**: Tacotron/Tacotron2, Glow-TTS, VITS, FastSpeech/FastPitch, AlignTTS, SpeedySpeech, DelightfulTTS, NeuralHMM, Overflow, XTTS, Bark, Tortoise, and related release variants.
- **Vocoder models**: HiFi-GAN, MelGAN, MultiBand MelGAN, Fullband MelGAN, Parallel WaveGAN, UnivNet, WaveGrad, WaveRNN.
- **Voice conversion**: FreeVC (`voice_conversion_models/multilingual/vctk/freevc24` is the distilled released model name used in this snapshot).

## How the skill is organized

- Root `SKILL.md` routes broad user requests to one of five sub-skills.
- `inference-and-model-zoo` owns Python API and registry behavior.
- `server-and-cli` owns installed command syntax and safe demo-server use.
- `training-config-data` owns dataset/config/training/fine-tuning preparation.
- `vocoder-and-audio-tools` owns audio preprocessing and vocoder preparation.
- `voice-conversion` owns FreeVC and TTS-with-VC workflows.

## Verified runtime facts

- The installed registry in this snapshot reported 88 models total: 70 TTS, 17 vocoder, and 1 voice-conversion entry.
- `tts --model_info_by_name tts_models/en/ljspeech/tacotron2-DDC` reports the default vocoder `vocoder_models/en/ljspeech/hifigan_v2`.
- `tts` and `tts-server` help output expose only the expected CLI flags and no unexpected package-level service surface.
- CUDA is available on the host used to build this skill, but the default package/import smoke does not require it.

## When to read more specific references

- Read the sub-skill references for exact API signatures, command templates, data schemas, troubleshooting, and bundled helper scripts.
- Read `references/troubleshooting.md` for cross-cutting install/import/version/audio/backend issues.
- Read `references/repo-provenance.md` before refreshing the skill or judging staleness.
