---
name: asr
description: "Use for NeMo Speech ASR model selection, checkpoint loading,
  transcription, timestamps, streaming, fine-tuning, Lhotse batching, decoding
  customization, and ASR evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ASR

Use this sub-skill for NeMo Speech automatic speech recognition tasks: selecting CTC/RNNT/TDT/Hybrid/AED Canary models, loading `.nemo` checkpoints or pretrained names, offline transcription, timestamps, long-audio inference, cache-aware or buffered streaming, fine-tuning, Lhotse/dynamic bucketing, tokenizer changes, decoding customization, confidence/LM/word boosting, and WER/BLEU-style ASR evaluation.

Route elsewhere when the task is primarily speaker diarization, VAD, or forced alignment; generic manifest sharding/tokenizer utilities; repository testing/formatting; or SpeechLM2/SALM duplex work. For generic data tooling, prefer `../data-tools/SKILL.md` when present; for repo workflows, prefer `../repo-development/SKILL.md` when present; for SpeechLM2, prefer `../speechlm2/SKILL.md` when present.

## Start Here

1. Read `references/workflows.md` for task-specific command and Python patterns.
2. Read `references/api-reference.md` before using model classes, `transcribe()`, timestamps, streaming pipeline builders, or decoding APIs.
3. Read `references/configuration.md` before editing Hydra YAML, manifests, Lhotse settings, tokenizer changes, Canary prompts, LM/customization, or evaluation settings.
4. Read `references/troubleshooting.md` when installs, CUDA/backends, Hydra overrides, manifests, Lhotse, streaming, decoding, or fine-tuning fail.

## Safe Bundled Tools

- `scripts/check_asr_manifest.py` validates small or large ASR JSONL manifests without importing NeMo, downloading models, touching audio contents, or writing outputs unless explicitly redirected by the caller.
- Run it before fine-tuning or evaluation manifests: `python scripts/check_asr_manifest.py train.jsonl --canary --min-duration 0.1 --max-duration 30`.

## Evidence Base

This sub-skill distills repository evidence from `docs/source/asr/inference.rst`, `docs/source/asr/fine_tuning.rst`, `docs/source/asr/configs.rst`, `docs/source/asr/datasets.rst`, `docs/source/asr/asr_language_modeling_and_customization.rst`, `docs/source/dataloaders.rst`, ASR example scripts/configs, ASR model/inference source, ASR tests, and the prior `.claude/skills/nemo-speech-asr-finetune/SKILL.md`. Runtime guidance is self-contained; do not require future agents to reopen those source files.
