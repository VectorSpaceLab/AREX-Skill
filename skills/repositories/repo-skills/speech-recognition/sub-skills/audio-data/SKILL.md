---
name: audio-data
description: "Use SpeechRecognition 3.17.0 file audio loading and AudioData
  conversion/splitting without microphones or transcription services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# audio-data

Use this sub-skill for local file-based audio ingestion and `speech_recognition.AudioData` manipulation in SpeechRecognition 3.17.0.

Read these bundled references before acting:

- [API reference](references/api-reference.md) for `AudioFile`, `AudioData.from_file`, segmenting, splitting, byte formats, conversion rules, and FLAC converter behavior.
- [Workflows](references/workflows.md) for copy-pasteable local-file conversion, chunking, and in-memory loading patterns.
- [Troubleshooting](references/troubleshooting.md) for unsupported WAV/AIFF/FLAC files, converter failures, 24-bit/sample-width edge cases, split validation errors, and `librosa`/`numpy` `SetupError` handling.

Bundled helper scripts:

- [`scripts/audio_convert.py`](scripts/audio_convert.py): convert a local input audio file into RAW/WAV/AIFF/FLAC outputs, optionally segmenting and splitting first.
- [`scripts/audio_smoke.py`](scripts/audio_smoke.py): generate tiny synthetic WAV data and verify `AudioData`, `AudioData.from_file`, `AudioFile`, conversions, and `split()` without source-repo fixtures.

Route away from this sub-skill when the task is not local audio-data handling:

- Any `recognize_*` transcription/API/model call belongs to the `recognition-engines` sub-skill.
- Microphone capture, ambient-noise calibration, `listen()`, and background listening belong to `capture-listening`.
- `sprc` CLI usage, model downloads, and model cache/setup issues belong to `cli-model-setup`.
