---
name: transcription-cli
description: "Command-line WhisperX transcription workflows, safe command
  construction, and CLI troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# transcription-cli

Use this sub-skill when the user wants to run or construct `whisperx` command-line transcription workflows for audio files: model/device/compute selection, VAD tuning, alignment and diarization toggles, output format choices, logging flags, and cache/offline behavior.

Do not use this sub-skill for Python object orchestration, alignment internals, diarization model/token depth, or output schema details. Route those tasks to the sibling sub-skills listed below.

## Start here

1. Confirm the user is asking for CLI usage rather than Python APIs.
2. Identify the audio inputs, desired output directory/format, language/task, device, compute type, and whether model downloads, HF credentials, and network access are allowed.
3. Use the bundled safe builder before suggesting a long command when you only need to assemble flags:
   - [`scripts/build_whisperx_command.py`](scripts/build_whisperx_command.py): prints a shell-quoted `whisperx ...` command without running WhisperX, reading token values, checking audio files, downloading models, or writing outputs.
4. Then open the focused reference needed for the user's task:
   - [`references/cli-reference.md`](references/cli-reference.md): use for flag names, defaults, parser constraints, entry point facts, VAD/alignment/diarization/output/logging option surfaces, and version-specific gotchas.
   - [`references/workflows.md`](references/workflows.md): use for complete command recipes: basic CPU/GPU transcription, offline cache-only construction, multilingual examples, VAD selection, translation, diarization, and logging.
   - [`references/troubleshooting.md`](references/troubleshooting.md): use when a CLI command fails or is unsafe due to ffmpeg/audio decode, cache-only misses, CUDA/compute mismatches, OOM, `--no_align` conflicts, missing HF tokens, or Silero cache/network behavior.

## Route elsewhere

- Python ASR/model/audio APIs: `../asr-python-api/SKILL.md`.
- Forced-alignment model selection, word/character timestamp behavior, and alignment language internals: `../alignment-timestamps/SKILL.md`.
- Diarization API, speaker assignment details, Hugging Face model terms, and token-handling depth: `../diarization-speakers/SKILL.md`.
- Output JSON/subtitle schema, writer internals, subtitle line splitting, highlighting rendering, and validation of generated files: `../outputs-subtitles/SKILL.md`.

## Operating guardrails

- The real `whisperx` CLI performs model loading, VAD, ASR, optional alignment, optional diarization, and writes output files. Do not run it for planning-only tasks.
- `--model_cache_only True` prevents downloads but requires every needed ASR/alignment/diarization model to already exist in the chosen cache/model directory.
- `--diarize` can require a Hugging Face access token and accepted gated model terms. Never paste token values into commands; prefer environment-variable expansion such as `--hf_token $HF_TOKEN`.
- `--task translate` disables alignment in the CLI task implementation. Word-level subtitle options require alignment.
- `--no_align` conflicts with `--highlight_words True`, `--max_line_width`, and `--max_line_count`.
- VAD is enabled through the ASR pipeline. Default `--vad_method pyannote` uses the packaged VAD asset; `--vad_method silero` may use Torch Hub cache/network access.
