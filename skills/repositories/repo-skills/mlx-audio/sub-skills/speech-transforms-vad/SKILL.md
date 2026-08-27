---
name: speech-transforms-vad
description: "Use MLX Audio for speech enhancement, source separation, VAD,
  realtime turn detection, and shared audio I/O workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Speech Transforms and VAD

Use this sub-skill when the user needs audio enhancement, source separation, speech activity detection, realtime turn detection, or shared audio I/O and resampling guidance.

## Route Here For

- Speech enhancement and source separation.
- VAD and diarization-style turn detection.
- Server-side `server_vad` planning.
- Audio I/O, resampling, normalization, trimming, and fixture validation.
- Safe command planning for `mlx_audio.sts.generate` and VAD probes.

## Route Elsewhere

- For TTS generation or cloning, use `../tts-generation/`.
- For transcription, alignment, or WER, use `../stt-transcription/`.
- For server endpoints or conversion, use `../server-and-conversion/`.

## Fast Paths

- See `references/audio-io-and-dsp.md` for shared audio handling.
- See `references/vad-and-realtime.md` for turn detection and server-side VAD.
- See `references/troubleshooting.md` for audio, threshold, and dependency failures.
- Use `scripts/validate_audio_io.py` to confirm a tiny round trip.
- Use `scripts/vad_turn_detection_probe.py` to inspect synthetic VAD events.
- Use `scripts/sts_command_builder.py` to shape a safe enhancement command.
