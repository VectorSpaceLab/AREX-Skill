---
name: data-and-features
description: "ASRT data configuration, datalist, dictionary, WAV, and speech
  feature extraction operating guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# data-and-features

Use this sub-skill when an ASRT task involves dataset configuration, pinyin dictionaries, WAV metadata, or speech-feature extraction before model training, evaluation, prediction, or serving.

## Owns

- `asrt_config.json` structure and dataset section semantics.
- `dict.txt` tab-separated pinyin-to-symbol rows and pinyin-to-index mapping.
- ASRT wav-list and syllable-label line schemas.
- `DataLoader` data assembly behavior and `utils.config` cache behavior.
- WAV readers and byte decoding used before feature extraction.
- MFCC, Logfbank, Spectrogram, and SpecAugment feature behavior, including the 16 kHz constraint for spectrogram-style inputs.

## Route away

- Training, evaluation, prediction scripts, acoustic-model class selection, model weights, CTC, and tensor shapes beyond data/feature compatibility: use `acoustic-models`.
- Pinyin sequence to Chinese text decoding or language-model internals: use `language-model`.
- HTTP/gRPC request payloads, server/client execution, and SDK calls: use `serving-clients`.
- Full dataset downloads and interactive download helpers: treat as reference-only, not as a bundled runtime workflow.

## Operating path

1. Read [references/data-and-config.md](references/data-and-config.md) before editing or validating config, dict, datalist, or syllable labels.
2. Run [scripts/validate_asrt_config.py](scripts/validate_asrt_config.py) for self-contained structural validation of config/list/dict files.
3. Read [references/audio-and-features.md](references/audio-and-features.md) before diagnosing WAV metadata, 16 kHz failures, spectrogram shape, MFCC/Logfbank behavior, or SpecAugment randomness.
4. Run [scripts/inspect_audio_features.py](scripts/inspect_audio_features.py) for safe WAV and feature-shape inspection without importing ASRT.
5. Use [references/api-reference.md](references/api-reference.md) for quick schema/API reminders and [references/troubleshooting.md](references/troubleshooting.md) for failure diagnosis.

## Safety and boundaries

The bundled scripts are read-only validators/inspectors. They do not download corpora, record microphone audio, call servers, train models, or require an ASRT checkout. Provide user-owned config, dict, datalist, label, or WAV paths explicitly.