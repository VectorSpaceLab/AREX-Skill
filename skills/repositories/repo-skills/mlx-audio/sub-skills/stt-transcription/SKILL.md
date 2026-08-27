---
name: stt-transcription
description: "Use MLX Audio STT workflows for transcription, streaming ASR,
  hotwords, forced alignment, and WER evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# STT Transcription

Use this sub-skill when the user wants to transcribe audio, stream transcription results, inject hotwords or context, run forced alignment, or compute WER summaries.

## Route Here For

- CLI or Python speech-to-text generation.
- Streaming transcription and partial results.
- Context or hotword guidance.
- Forced alignment with an explicit transcript.
- WER evaluation and summary planning.
- Safe planning for `mlx_audio.stt.generate` and `mlx_audio.stt.eval`.

## Route Elsewhere

- For text-to-speech generation or voice cloning, use `../tts-generation/`.
- For audio enhancement, separation, VAD, or audio I/O, use `../speech-transforms-vad/`.
- For server endpoints or conversion, use `../server-and-conversion/`.

## Fast Paths

- See `references/workflows.md` for transcription, alignment, streaming, and WER recipes.
- See `references/api-reference.md` for stable kwargs and output-format facts.
- See `references/troubleshooting.md` for audio path, JSON, and alignment failures.
- Use `scripts/stt_command_builder.py` to shape a safe CLI command.
- Use `scripts/wer_summary.py` to summarize simple WER pairs or line-aligned fixtures.

## Default Safety Policy

Confirm the audio path, output format, and whether the model needs a transcript or context before a long run. If the user only needs a command plan, prefer the bundled builders and docs over a live inference call.
