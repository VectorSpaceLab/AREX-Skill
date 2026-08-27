---
name: asr-python-api
description: "Use WhisperX's Python API for ASR model loading, audio arrays,
  VAD-batched transcription, progress callbacks, local cache use, and
  device/memory tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# WhisperX ASR Python API

Use this sub-skill when a task needs WhisperX through Python code rather than the `whisperx` command line: importing the package, loading ASR models, representing audio as paths or NumPy arrays, running VAD-batched transcription, reporting progress, using local model caches, or choosing device/compute/memory settings.

Do **not** use this sub-skill for:

- CLI flag catalogs or command construction; route to `../transcription-cli/`.
- Forced alignment, word/character timestamps, or alignment models; route to `../alignment-timestamps/` after ASR segments exist.
- Diarization or speaker labels; route to `../diarization-speakers/` after ASR or alignment results exist.
- Rendering JSON/SRT/VTT/TXT/TSV/Audacity files; route to `../outputs-subtitles/` after result dictionaries exist.

## Read first

- [`references/api-reference.md`](references/api-reference.md) — use when you need verified Python signatures, return schemas, `TranscriptionResult` fields, audio constants, or ASR/VAD option names.
- [`references/workflows.md`](references/workflows.md) — use when you need self-contained Python recipes for path audio, cached NumPy-array transcription, progress callbacks, and memory-conscious runs.
- [`references/model-and-backend-notes.md`](references/model-and-backend-notes.md) — use before choosing `device`, `compute_type`, `batch_size`, `download_root`, `local_files_only`, VAD method, language, or cache behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md) — use when imports, ffmpeg audio loading, model cache/downloads, CUDA/compute type, low memory, CPU slowness, language detection, `suppress_numerals`, or cache-only operation fails.

## Safe bundled helpers

- [`scripts/inspect_whisperx_api.py`](scripts/inspect_whisperx_api.py) — run for a no-download import/signature report, public lazy API presence, package version, and torch CUDA availability. It intentionally does not call `load_model` or `transcribe`.
- [`scripts/check_audio_loading.py`](scripts/check_audio_loading.py) — run for a tiny generated-WAV `whisperx.load_audio` smoke check. It writes only to a temporary directory and catches missing `ffmpeg`.

## Operating facts

- Distribution/package version covered by this skill: `whisperx 3.8.7rc1`; import name: `whisperx`.
- Supported Python range from package metadata: `>=3.10,<3.14`.
- Public top-level functions such as `whisperx.load_model` and `whisperx.load_audio` are lazy wrappers; use the source signatures in the API reference for real arguments.
- Full ASR execution may download model weights unless the caller intentionally uses `local_files_only=True` with a populated cache. The bundled helpers are safe by default and do not run model inference.

## Minimal routing pattern

1. Inspect the runtime surface with `python scripts/inspect_whisperx_api.py` if the environment is unknown.
2. For path audio, confirm `ffmpeg` or run `python scripts/check_audio_loading.py`; for already-decoded audio, provide a mono `float32` NumPy array sampled at 16 kHz.
3. Load ASR with `whisperx.load_model(...)`, choosing cache and backend settings from `model-and-backend-notes.md`.
4. Call `model.transcribe(audio, ...)` and treat the returned object as `TranscriptionResult`: `{"segments": [...], "language": "..."}`.
5. Route any post-ASR alignment, diarization, or file rendering to the sibling sub-skills above.
