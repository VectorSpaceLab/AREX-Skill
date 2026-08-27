---
name: tts
description: "Use for NeMo Speech TTS synthesis, FastPitch and HiFi-GAN
  cascades, MagpieTTS and EasyMagpie inference or finetuning, G2P, audio codecs,
  TTS manifests, preprocessing, evaluation, and TTS troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TTS

Use this sub-skill for NeMo Speech text-to-speech work: cascaded FastPitch/HiFi-GAN synthesis, MagpieTTS and EasyMagpie inference or finetuning, G2P conversion and training, audio codec training, text and phoneme preprocessing, checkpoint compatibility, manifest validation, TTS evaluation, and TTS-specific troubleshooting.

Route generic audio enhancement/restoration/separation to `../audio/SKILL.md`. Route generic manifest sharding, tokenizer building, and dataset conversion utilities to `../data-tools/SKILL.md` when present. Route SpeechLM2 voice-chat, SALM, and duplex speech-language modeling to `../speechlm2/SKILL.md`. Route repository testing, formatting, packaging, or CI tasks to `../repo-development/SKILL.md` when present.

## Start Here

1. Read `references/model-overview.md` to choose FastPitch/HiFi-GAN, MagpieTTS/EasyMagpie, G2P, audio codec, aligner, SSL TTS, or preference-optimization workflows.
2. Read `references/data-formats.md` before creating or auditing TTS, MagpieTTS, G2P, vocoder, or audio-codec manifests and dataset metadata.
3. Read `references/workflows.md` for concrete Python, Hydra, inference, finetuning, G2P, codec, and evaluation contracts.
4. Read `references/troubleshooting.md` when installation, CUDA, optional dependencies, text normalization, phonemization, checkpoint loading, Hydra overrides, long-form inference, or evaluation metrics fail.

## Safe Bundled Tool

- `scripts/check_tts_manifest.py` validates TTS/G2P-style JSONL manifests without importing NeMo, opening audio contents, downloading models, training, or writing outputs.
- Run it from this sub-skill directory before training, finetuning, evaluation, or batch inference: `python scripts/check_tts_manifest.py train.jsonl --mode tts --require-audio --check-files --min-duration 0.1 --max-duration 30`.
- For G2P manifests: `python scripts/check_tts_manifest.py g2p_train.jsonl --mode g2p --grapheme-field text_graphemes --phoneme-field text`.
- For MagpieTTS context manifests: `python scripts/check_tts_manifest.py magpie.jsonl --mode magpie --require-audio --require-context --style-summary`.

## Evidence Base

This sub-skill distills repository evidence from TTS docs, TTS example scripts/configs, `nemo.collections.tts` model/data/G2P source, and TTS tests. Runtime guidance is self-contained; do not require future agents to reopen original source docs, examples, scripts, or tests.
