---
name: speech-recognition
description: "Guides SpeechRecognition package workflows for audio loading,
  microphone capture, speech recognizer engines, CLI/model setup, and repository
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SpeechRecognition Repo Skill

Use this repo skill when a task involves the Python `SpeechRecognition` package: local audio file handling, microphone capture, choosing a speech-to-text engine, setting up optional recognizer dependencies, using the `sprc` CLI, or maintaining the package repository.

## Quick package facts

- Public distribution: `SpeechRecognition`
- Import package: `speech_recognition`
- Supported Python: `>=3.10`
- Console script: `sprc`
- Current distilled version: `3.17.0`
- Minimal install:

  ```bash
  python -m pip install SpeechRecognition
  python - <<'PY'
  import speech_recognition as sr
  print(sr.__version__)
  print(sr.Recognizer())
  PY
  ```

Read [references/repo-provenance.md](references/repo-provenance.md) before checking freshness against a checkout or deciding whether to refresh this skill. Read [references/package-overview.md](references/package-overview.md) for package identity, optional extras, public entry points, and scope boundaries. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, FLAC, optional dependency, credential, and CLI failures.

For a non-invasive runtime probe, run:

```bash
python scripts/check_install.py --json
```

## Route by task

| User task | Read |
| --- | --- |
| Load WAV/AIFF/FLAC files, create `AudioData`, convert to raw/WAV/AIFF/FLAC bytes, segment or split oversized audio | [audio-data](sub-skills/audio-data/SKILL.md) |
| Capture microphone input, calibrate ambient noise, use `record`, `listen`, streaming chunks, background callbacks, or threaded capture | [capture-listening](sub-skills/capture-listening/SKILL.md) |
| Choose or call a transcription engine such as Google, PocketSphinx, Vosk, Whisper, OpenAI-compatible, Groq, Cohere, Google Cloud, or legacy APIs | [recognition-engines](sub-skills/recognition-engines/SKILL.md) |
| Install extras, check optional dependencies, use `sprc`, set up Vosk model files, or debug CLI/model setup | [cli-model-setup](sub-skills/cli-model-setup/SKILL.md) |
| Edit or review the SpeechRecognition repository, choose focused tests, update docs/examples, or reason about CI/release/FLAC packaging | [repo-development](sub-skills/repo-development/SKILL.md) |

## Common operating sequence

1. **Get audio.** Use `audio-data` for existing files or `capture-listening` for live microphone input. Both produce `speech_recognition.AudioData`.
2. **Prepare environment/model needs.** Use `cli-model-setup` to install the exact extra for the chosen workflow and to check `sprc`/Vosk/optional imports without unsafe downloads.
3. **Transcribe.** Use `recognition-engines` to pick one engine and handle its parameters, credentials, return shape, and errors.
4. **Validate or debug.** Use the nearest sub-skill troubleshooting reference; use root troubleshooting only for cross-cutting install, FLAC, CLI, or optional-dependency failures.
5. **If editing the repo itself,** switch to `repo-development` and choose tests from the changed surface instead of using end-user workflows as maintainer checks.

## Key boundaries

- This skill is for using and maintaining the SpeechRecognition package. It does not provide general ASR model training, diarization, TTS, or benchmark guidance outside the package's public surfaces.
- Optional engines are not base requirements. Install only the extra for the engine or workflow the user actually needs.
- Cloud/API recognizers need credentials and network access. Do not store secrets in code, skill files, or review artifacts.
- Microphone capture needs PyAudio/PortAudio plus real input hardware. Do not run interactive microphone commands in headless automation.
- `sprc download vosk` performs network download and writes into the installed package's model directory; ask before running it in a user environment.
- Runtime instructions here are self-contained. Do not rely on original repository examples or docs remaining available unless the task is explicitly repository maintenance in a checkout.
