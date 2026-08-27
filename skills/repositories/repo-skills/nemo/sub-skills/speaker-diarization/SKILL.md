---
name: speaker-diarization
description: "Use for NeMo Speech speaker recognition, diarization, VAD,
  Sortformer, speaker embeddings, ASR+diarization scoring, forced alignment,
  RTTM/CTM manifests, and speaker workflow troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Speaker Diarization

Use this sub-skill for NeMo Speech speaker workflows: speaker recognition and verification, speaker embedding extraction, clustering diarization, Sortformer end-to-end diarization, VAD-backed diarization, ASR plus diarization transcript scoring, forced alignment manifests and CTM/ASS outputs, RTTM handling, and speaker workflow troubleshooting.

Route elsewhere when the task is mostly general ASR transcription, ASR fine-tuning, or decoding; generic manifest sharding/tokenizer utilities; audio enhancement; or repository build/test work. For ASR model selection, decoding, timestamps, and fine-tuning, use `../asr/SKILL.md`.

## Start Here

1. Read `references/workflows.md` to choose between Sortformer, clustering diarization, speaker recognition, VAD, ASR+diarization, and forced-alignment workflows.
2. Read `references/data-formats.md` before creating or debugging manifests, RTTM, CTM, UEM, speaker labels, or output file paths.
3. Read `references/forced-alignment.md` for NeMo Forced Aligner concepts, manifest requirements, CTM/ASS output contracts, and EOU alignment notes.
4. Read `references/troubleshooting.md` when imports, optional dependencies, CUDA, manifests, Hydra overrides, VAD/clustering, Sortformer, ASR+diarization, or forced alignment fail.
5. Run `scripts/check_speaker_manifest.py --help` before long diarization, recognition, VAD, or forced-alignment runs.

## Safe Bundled Tool

- `scripts/check_speaker_manifest.py` validates JSONL manifests and common output path fields without importing NeMo, reading audio, downloading checkpoints, training, or writing outputs.
- Example: `python scripts/check_speaker_manifest.py manifest.json --task diarization-eval --require-rttm --check-rttm-speakers --require-matching-basename`.

## Core Facts

- Installed package evidence verified `nemo-toolkit` version `3.1.0+8f85359` from editable source-backed code. NeMo Speech docs currently target Python 3.12+, PyTorch 2.7+, and GPU/CUDA for training; GPU is strongly recommended for inference.
- Speaker recognition uses `nemo.collections.asr.models.EncDecSpeakerLabelModel` for TitaNet, ECAPA-TDNN, SpeakerNet, embeddings, verification, and batch inference.
- End-to-end diarization uses `nemo.collections.asr.models.SortformerEncLabelModel`; offline and streaming Sortformer variants emit speaker segments such as `[begin_seconds, end_seconds, speaker_index]`.
- Cascaded diarization uses `nemo.collections.asr.models.ClusteringDiarizer` with VAD, speaker embeddings, and clustering. It can also combine ASR word timestamps with diarization labels for speaker-attributed transcripts and cpWER-style evaluation.
- Forced alignment uses CTC ASR models to align audio to reference text or ASR-predicted text and can emit CTM and ASS outputs. The long source aligner scripts are reference-only in this skill; use the bundled references for config and data contracts.

## Evidence Base

This sub-skill distills repository evidence from `docs/source/asr/speaker_diarization/**`, `docs/source/asr/speaker_recognition/**`, `docs/source/asr/speech_classification/**`, `examples/speaker_tasks/**`, `scripts/speaker_tasks/**`, `scripts/voice_activity_detection/**`, `tools/nemo_forced_aligner/**`, `nemo/collections/asr/models/label_models.py`, `nemo/collections/asr/models/sortformer_diar_models.py`, `tests/collections/speaker_tasks/**`, and `tools/nemo_forced_aligner/tests/**`. Runtime guidance is self-contained; future agents should not need to reopen those source files.
