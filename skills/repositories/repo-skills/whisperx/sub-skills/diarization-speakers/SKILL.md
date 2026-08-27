---
name: diarization-speakers
description: "Use WhisperX diarization APIs and safe offline speaker-label
  assignment for transcript segments and words."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# diarization-speakers

Use this sub-skill when a task is about WhisperX speaker diarization setup, Hugging Face pyannote access, diarization speaker-count constraints, or assigning speaker labels to existing transcript segments/words.

Route elsewhere for adjacent work:

- Produce ASR transcripts or call WhisperX ASR/audio loading: use `asr-python-api`.
- Produce or repair word timestamps/alignment before speaker assignment: use `alignment-timestamps`.
- Render speaker labels into JSON/SRT/VTT/TXT/TSV/Audacity files: use `outputs-subtitles` after labels are assigned.
- Generic CUDA/cuDNN/PyTorch installation failures: use the root WhisperX troubleshooting reference, then return here for diarization-specific choices.

## What to read

- [API reference](references/api-reference.md): use when choosing `DiarizationPipeline`, `assign_word_speakers`, `IntervalTree`, `Segment`, or CLI diarization flags.
- [Workflows](references/workflows.md): use for safe CLI/Python diarization recipes, offline assignment from CSV, `fill_nearest`, and speaker embeddings.
- [Data formats](references/data-formats.md): use when validating transcript JSON, diarization CSV/DataFrame columns, speaker labels, or overlap behavior.
- [Troubleshooting](references/troubleshooting.md): use for token/model access, gated pyannote terms, speaker-count constraints, empty diarization rows, missing overlaps, embeddings, and CPU/GPU device choices.
- [assign_speakers_from_csv.py](scripts/assign_speakers_from_csv.py): use when the user already has transcript JSON plus diarization intervals and needs speaker assignment without model downloads, Hugging Face tokens, or `DiarizationPipeline` instantiation.

## Fast operating rules

1. Separate model-backed diarization from offline speaker assignment. `DiarizationPipeline` may access a pyannote model; `assign_word_speakers` only applies already-known speaker intervals to a transcript.
2. For model-backed diarization, confirm whether the user has a Hugging Face read token, accepted the selected pyannote model terms, and intentionally chose CPU or GPU.
3. For existing transcript JSON plus diarization CSV, prefer the bundled assignment helper. It validates `start,end,speaker` rows and calls WhisperX assignment safely.
4. Never ask the user to paste secrets into chat or logs. Treat tokens as external secrets and redact them from commands, notebooks, reports, and examples.
5. If speaker labels are missing, first check whether diarization intervals overlap transcript segment/word timestamps. Use `fill_nearest` only for small timing drift or known sparse intervals, not to hide a failed diarization run.
