---
name: tts-generation
description: "Use MLX Audio TTS workflows for generation, voice cloning,
  streaming, batching, and model-specific controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TTS Generation

Use this sub-skill when the user wants to synthesize speech from text, clone a voice from a reference clip, stream audio during generation, or choose the right TTS model family and flags.

## Route Here For

- Basic text-to-speech generation from CLI or Python.
- Voice cloning with `ref_audio` and optional `ref_text`.
- Streaming output, chunk joining, save behavior, and playback planning.
- Model-family questions for Kokoro, Qwen3-TTS, OmniVoice, Higgs Audio, CSM / MisoTTS, Spark, Ming Omni, Voxtral TTS, Chatterbox, and other TTS models shipped by the package.
- Safe command planning for `mlx_audio.tts.generate`.

## Route Elsewhere

- For transcription, forced alignment, streaming ASR, or WER, use `../stt-transcription/`.
- For enhancement, separation, VAD, or audio I/O, use `../speech-transforms-vad/`.
- For server endpoints or conversion, use `../server-and-conversion/`.

## Fast Paths

- See `references/workflows.md` for the main TTS recipes.
- See `references/api-reference.md` for stable kwargs and model-loading facts.
- See `references/troubleshooting.md` for import, playback, and cloning failures.
- Use `scripts/tts_command_builder.py` to shape a safe CLI command before a long run.

## Default Safety Policy

Prefer a small reproducible recipe first: confirm the model id, confirm the reference clip path, confirm whether the model requires `ref_text`, and then decide whether streaming or file saving is actually needed. If the task is only about a command plan, do not start an inference run.
