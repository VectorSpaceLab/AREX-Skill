# SpeechRecognition Package Overview

## Identity and public surfaces

| Item | Value |
| --- | --- |
| Distribution name | `SpeechRecognition` |
| Import package | `speech_recognition` |
| Console script | `sprc` |
| Python requirement | `>=3.10` |
| Distilled package version | `3.17.0` |
| Core objects | `Recognizer`, `AudioFile`, `AudioData`, `Microphone`, `AudioSource` |
| Common exceptions | `UnknownValueError`, `RequestError`, `SetupError`, `WaitTimeoutError`, `TranscriptionNotReady`, `TranscriptionFailed` |

The package is a speech-recognition convenience library. It does not train ASR models; it converts/captures audio and sends or adapts that `AudioData` to local engines, local model wrappers, and web/cloud APIs.

## Minimal install and import check

```bash
python -m pip install SpeechRecognition
python - <<'PY'
import speech_recognition as sr
print(sr.__version__)
print(sr.AudioData(b"\0\0", 16000, 2).sample_rate)
print(hasattr(sr.Recognizer(), "recognize_google"))
PY
```

Python 3.13 and newer need compatibility packages for modules removed from the standard library. Installing through package metadata should resolve these dependencies automatically.

## Optional extras by workflow

Install only the extra needed for the selected task:

| Workflow | Install command | Notes |
| --- | --- | --- |
| Microphone input | `python -m pip install "SpeechRecognition[audio]"` | Adds PyAudio; host PortAudio and real input hardware may still be needed. |
| PocketSphinx offline ASR | `python -m pip install "SpeechRecognition[pocketsphinx]"` | Uses bundled English data by default; other languages need language data. |
| Vosk offline ASR | `python -m pip install "SpeechRecognition[vosk]"` | Also needs a Vosk model prepared with `sprc download vosk` or manual model placement. |
| Google Cloud Speech-to-Text | `python -m pip install "SpeechRecognition[google-cloud]"` | Requires Google Cloud authentication and enabled API. |
| Local Whisper | `python -m pip install "SpeechRecognition[whisper-local]"` | First model load can download/cache weights; upstream stack may need FFmpeg. |
| Faster-Whisper | `python -m pip install "SpeechRecognition[faster-whisper]"` | CPU works for API wiring; performance may require accelerator support. |
| OpenAI-compatible API | `python -m pip install "SpeechRecognition[openai]"` | Uses OpenAI SDK; supports custom `OPENAI_BASE_URL`. |
| Groq API | `python -m pip install "SpeechRecognition[groq]"` | Requires Groq SDK authentication. |
| Cohere API | `python -m pip install "SpeechRecognition[cohere-api]"` | `recognize_cohere_api` requires a language argument. |
| AssemblyAI method | `python -m pip install "SpeechRecognition[assemblyai]"` | Uses `requests` and service token. |
| Silence-aware audio splitting | `python -m pip install "SpeechRecognition[audio-split]"` | Adds `librosa`/`numpy` for `AudioData.split(..., silence_aware=True)`. |
| Maintainer tests | `python -m pip install "SpeechRecognition[dev]"` | Adds pytest/respx/mypy-related test dependencies. |

The `sprc` CLI in 3.17.0 imports `tqdm` unconditionally. If `sprc --help` fails with a missing `tqdm` import, install `tqdm` in the same environment.

## Package data and runtime assets

- The package includes `version.txt` and platform-specific FLAC converter binaries for common Windows, Linux, and macOS x86 cases.
- Default PocketSphinx English data is package data.
- Vosk model files are not shipped in the base package; the CLI writes them into the installed package's `speech_recognition/models/vosk` directory.
- `speech_recognition/models/` is a runtime model location, not source material to copy into generated skills.

## Capability boundaries

- `audio-data` owns file/audio bytes, formats, conversion, and split/chunk logic.
- `capture-listening` owns microphone and live `AudioSource` capture.
- `recognition-engines` owns recognizer methods and transcription errors.
- `cli-model-setup` owns installation, optional extras, `sprc`, and model setup.
- `repo-development` owns contributor/testing/release guidance for a checkout.
