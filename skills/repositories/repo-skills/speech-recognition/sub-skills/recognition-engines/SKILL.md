---
name: recognition-engines
description: "Recognizer engine selection and transcription APIs for
  SpeechRecognition 3.17.0."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Recognition Engines

Use this sub-skill when a task is about choosing or calling a SpeechRecognition recognizer engine, interpreting transcription return values, or diagnosing engine-specific optional dependency, credential, language, model, or network failures.

## Use this for

- `Recognizer.recognize_google`, `recognize_google_cloud`, `recognize_sphinx`, `recognize_vosk`, `recognize_whisper`, `recognize_faster_whisper`, `recognize_openai`, `recognize_groq`, and `recognize_cohere_api`.
- Legacy/service methods still present on `Recognizer`: `recognize_wit`, `recognize_azure`, `recognize_houndify`, `recognize_ibm`, `recognize_amazon`, `recognize_lex`, `recognize_assemblyai`, `recognize_tensorflow`, and `recognize_api`.
- `show_all`, `verbose`, `show_dict`, confidence tuple variants, raw response objects, and `UnknownValueError` versus `RequestError` versus `SetupError` handling.
- Optional extras, SDK credentials, local Sphinx/Vosk/Whisper/Faster-Whisper model notes, and OpenAI-compatible base URL setup.

## Route elsewhere

- File loading, `AudioData` conversion, segmentation, upload-size chunking, WAV/AIFF/FLAC details: route to [`audio-data`](../audio-data/SKILL.md).
- Microphone acquisition, calibration, `listen`, background callbacks, and capture-time thresholds: route to [`capture-listening`](../capture-listening/SKILL.md).
- `sprc download vosk`, CLI help, environment probes, and model-download side effects: route to [`cli-model-setup`](../cli-model-setup/SKILL.md).
- Repository edits, recognizer tests, CI, docs updates, and maintainer workflows: route to [`repo-development`](../repo-development/SKILL.md).

## Read first

1. [`references/engine-selection.md`](references/engine-selection.md) to choose a local, default web, cloud SDK, OpenAI-compatible, or legacy engine.
2. [`references/api-reference.md`](references/api-reference.md) for verified signatures, parameters, return shapes, and exceptions.
3. [`references/cloud-and-engine-reference.md`](references/cloud-and-engine-reference.md) for optional extras, credentials, local model requirements, and raw response behavior.
4. [`references/troubleshooting.md`](references/troubleshooting.md) when an engine fails or returns no transcript.

## Bundled helpers

- [`scripts/transcribe_file.py`](scripts/transcribe_file.py): inspect an audio file without network access by default, or transcribe a user-supplied file with an explicitly selected engine.
- [`scripts/sphinx_keyword_grammar_template.py`](scripts/sphinx_keyword_grammar_template.py): PocketSphinx keyword and grammar template with argument validation and no bundled source-example dependency.

These helpers are examples/templates. They read user-supplied audio paths and the installed SpeechRecognition package; they do not require the original source repository.
