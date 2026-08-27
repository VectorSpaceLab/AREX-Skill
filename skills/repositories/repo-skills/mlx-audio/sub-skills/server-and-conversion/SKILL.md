---
name: server-and-conversion
description: "Use MLX Audio for the API server, realtime WebSockets, Studio UI
  launch, and conversion or quantization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Server and Conversion

Use this sub-skill when the user needs the FastAPI/OpenAI-compatible server, realtime speech endpoints, Studio UI launch, or model conversion and quantization.

## Route Here For

- `mlx_audio.server` startup, API routes, and realtime WebSocket behavior.
- OpenAI-compatible speech and transcription endpoints.
- Server-side VAD and realtime turn detection configuration.
- `mlx_audio.convert` conversion, quantization, dequantization, and upload planning.
- Safe smoke checks against a running server.

## Route Elsewhere

- For TTS generation or cloning, use `../tts-generation/`.
- For transcription, alignment, or WER, use `../stt-transcription/`.
- For audio enhancement, separation, VAD, or audio I/O, use `../speech-transforms-vad/`.

## Fast Paths

- See `references/server-api.md` for the endpoint map and realtime model-selection rules.
- See `references/conversion.md` for conversion and quantization flags.
- See `references/troubleshooting.md` for dependency, protocol, and flag-mix failures.
- Use `scripts/server_smoke_client.py` to ping a running server.
- Use `scripts/convert_command_builder.py` to shape a safe conversion command.

## Default Safety Policy

Treat the server and conversion paths as command-planning workflows first. Confirm the API surface, model id, response format, and quantization intent before starting a long-running server or conversion job.
