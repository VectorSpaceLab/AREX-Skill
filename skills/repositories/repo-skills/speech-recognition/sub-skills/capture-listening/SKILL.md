---
name: capture-listening
description: "Guides SpeechRecognition microphone and streaming capture
  workflows with Microphone, record, listen, background callbacks, calibration,
  device listing, thresholds, and output capture."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Capture and Listening

Use this sub-skill when the task is to obtain audio from a microphone or other live `AudioSource` before transcription: choosing devices, calibrating ambient noise, using `Recognizer.record`, `Recognizer.listen`, `listen(stream=True)`, or `listen_in_background`, handling thresholds, and saving captured audio for later use.

## Route here for

- Listing microphones and selecting `Microphone(device_index=...)`.
- Building interactive microphone capture flows with `timeout`, `phrase_time_limit`, calibration, and optional WAV output.
- Distinguishing fixed-duration capture with `record` from speech-boundary capture with `listen`.
- Streaming chunk capture with `listen(stream=True)`.
- Background capture callbacks, worker queues, and safe stopper patterns.
- Diagnosing PyAudio, default-device, threshold, blocking, ALSA/JACK, and callback-thread issues.

## Route elsewhere

- Audio file formats, `AudioData` conversion methods, splitting, FLAC/WAV/AIFF details, and file-input workflows: use the sibling `audio-data` sub-skill.
- Recognition engines, language options, remote-service setup, network/model errors, and transcription output: use the sibling `recognition-engines` sub-skill.
- Installing PyAudio/PortAudio extras, the `sprc` console script, model downloads, and cross-cutting package setup: use the root skill or sibling `cli-model-setup` sub-skill.

## Read next

- Read [references/workflows.md](references/workflows.md) for verified API facts, capture recipes, threshold tuning, streaming/background patterns, and safe output capture.
- Read [references/troubleshooting.md](references/troubleshooting.md) when microphone capture fails, hangs, triggers on noise, misses speech, or has background-thread issues.
- Use [scripts/microphone_capture_template.py](scripts/microphone_capture_template.py) as a safe interactive template. It supports `--help` without PyAudio, `--list-devices`, capture time limits, and optional WAV output without recognition-engine calls.

## Operating reminders

- Always open `Microphone` or another `AudioSource` with a `with` block before calling `record`, `listen`, or `adjust_for_ambient_noise`; `listen_in_background` opens the source internally.
- Calibrate with `adjust_for_ambient_noise` during silence before a first `listen` when ambient noise is unknown.
- Keep capture separate from transcription. Capture returns `AudioData`; pass it to an engine only after selecting the correct recognition sub-skill.
- Treat microphone examples as hardware-only native candidates; do not execute them automatically in headless verification.
