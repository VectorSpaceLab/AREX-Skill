---
name: whisperx
description: "Operate WhisperX speech transcription, forced alignment,
  diarization, VAD, and subtitle/output workflows through CLI and Python APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# WhisperX

Use this repo skill when a task involves WhisperX time-accurate automatic speech recognition: CLI transcription, Python ASR APIs, VAD-batched audio handling, forced word/character alignment, speaker diarization, or transcript/subtitle output rendering.

WhisperX wraps faster-whisper/CTranslate2 ASR, VAD preprocessing, wav2vec2 forced alignment for word timestamps, optional pyannote speaker diarization, and writers for text, JSON, TSV, SRT, VTT, and Audacity labels.

## First checks

1. Confirm the task is about using WhisperX rather than editing unrelated speech repositories.
2. Check whether the user wants CLI commands, Python code, alignment timestamps, diarization speakers, or output/subtitle files.
3. Confirm side-effect boundaries: model downloads, network access, Hugging Face tokens, CUDA/GPU use, output directory writes, and long audio runtime.
4. If the runtime environment is unknown, run the bundled safe check:
   - [`scripts/check_whisperx_environment.py`](scripts/check_whisperx_environment.py) verifies package import, distribution version, CLI help/version, ffmpeg presence, core submodule imports, and optional torch CUDA visibility without loading ASR/alignment/diarization models.

## Install and runtime baseline

Typical install:

```bash
pip install whisperx
```

For local tool execution, `uvx whisperx` is also documented by the project. The covered package baseline is `whisperx 3.8.7rc1` with Python `>=3.10,<3.14`. Path-based audio loading requires the `ffmpeg` executable. GPU acceleration requires a compatible PyTorch/CTranslate2/CUDA/cuDNN stack; CPU operation should normally use `--device cpu --compute_type int8` for CLI commands or `device="cpu"` with an explicit compute type in Python.

Minimal import check:

```bash
python - <<'PY'
import whisperx
print(hasattr(whisperx, "load_model"), hasattr(whisperx, "align"))
PY
```

## Route by task

| User task | Open this sub-skill |
| --- | --- |
| Build, validate, or troubleshoot `whisperx ...` command-line transcription commands | [`sub-skills/transcription-cli/SKILL.md`](sub-skills/transcription-cli/SKILL.md) |
| Write Python code using `load_model`, `load_audio`, `FasterWhisperPipeline.transcribe`, VAD-batched ASR, progress callbacks, or model caches | [`sub-skills/asr-python-api/SKILL.md`](sub-skills/asr-python-api/SKILL.md) |
| Select alignment models, run `load_align_model` / `align`, understand word/char timestamp schemas, or debug missing numeric-word timestamps | [`sub-skills/alignment-timestamps/SKILL.md`](sub-skills/alignment-timestamps/SKILL.md) |
| Use pyannote diarization, handle Hugging Face model access, assign speaker labels, or post-process diarization CSV intervals | [`sub-skills/diarization-speakers/SKILL.md`](sub-skills/diarization-speakers/SKILL.md) |
| Validate transcript result JSON, write SRT/VTT/TXT/TSV/JSON/Audacity outputs, tune word highlighting, or split subtitles | [`sub-skills/outputs-subtitles/SKILL.md`](sub-skills/outputs-subtitles/SKILL.md) |

## Shared references

- [`references/backend-and-environment.md`](references/backend-and-environment.md): read before choosing CPU/CUDA/MPS, installing PyTorch variants, relying on model caches, or diagnosing optional runtime prerequisites.
- [`references/troubleshooting.md`](references/troubleshooting.md): read for cross-cutting install/import, ffmpeg, CUDA/cuDNN, cache-only, diarization-token, VAD, and output-routing failures.
- [`references/repo-provenance.md`](references/repo-provenance.md): read before deciding whether this skill is current for a checkout or whether to run `refresh-repo-skill`.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): structured scenario metadata for managed repo-skill import.

## Operating guardrails

- Do not run real transcription, alignment model downloads, diarization model loading, or Silero Torch Hub loading just to answer a planning question. Use the safe helper scripts and references first.
- Never paste Hugging Face token values into commands, notebooks, reports, or messages. Use environment-variable placeholders such as `$HF_TOKEN`.
- `--task translate` disables alignment in the CLI implementation, so word-level subtitle options are invalid for translation commands.
- Word highlighting, max-line options, and most precise subtitle timing require alignment-derived `words[].start` / `words[].end` fields.
- Real ASR, alignment, and diarization quality depends on model caches, language/model choice, audio quality, VAD thresholds, hardware, and optional credentials; distinguish command/API correctness from acoustic accuracy.
- Keep generated examples self-contained. If a user asks for an executable helper, use scripts bundled in this skill tree rather than pointing to the original repository checkout.
