# Optional dependencies and install groups

SpeechRecognition 3.17.0 uses distribution name `SpeechRecognition`, import
package `speech_recognition`, console script `sprc`, and Python `>=3.10`.
Install the base package with:

```bash
python -m pip install SpeechRecognition
python - <<'PY'
import speech_recognition as sr
print(sr.Recognizer())
PY
```

On Python 3.13+, the package metadata adds compatibility packages for standard
library modules that were removed or deprecated: `standard-aifc` and
`audioop-lts`. If imports fail for `aifc` or `audioop`, reinstall through the
package metadata rather than importing a raw checkout.

## Official extras grouped by workflow

| Workflow | Install command | Optional modules checked | Extra setup needed | Owning route |
| --- | --- | --- | --- | --- |
| Microphone capture | `python -m pip install "SpeechRecognition[audio]"` | `pyaudio` | Host PortAudio headers/runtime and a real input device. | [capture-listening](../../capture-listening/SKILL.md) |
| PocketSphinx offline recognition | `python -m pip install "SpeechRecognition[pocketsphinx]"` | `pocketsphinx` | Build/runtime audio libraries may be needed on some Linux installs; default English data is bundled. | [recognition-engines](../../recognition-engines/SKILL.md) |
| Vosk offline recognition | `python -m pip install "SpeechRecognition[vosk]"` | `vosk` | Run `sprc download vosk` after accepting network/download/write side effects. | [CLI reference](cli-reference.md) then [recognition-engines](../../recognition-engines/SKILL.md) |
| Google Cloud Speech-to-Text V1 | `python -m pip install "SpeechRecognition[google-cloud]"` | `google.cloud.speech` | Google Cloud project, enabled API, billing, and local application authentication or an authentication JSON path. | [recognition-engines](../../recognition-engines/SKILL.md) |
| Local Whisper | `python -m pip install "SpeechRecognition[whisper-local]"` | `whisper`, `soundfile` | First model use can download/cache weights; ffmpeg is commonly required by the upstream stack. Prefer Python 3.10-3.13 for this extra. | [recognition-engines](../../recognition-engines/SKILL.md) |
| Faster-Whisper | `python -m pip install "SpeechRecognition[faster-whisper]"` | `faster_whisper`, `soundfile` | First model use can download/cache weights; CPU is usable but performance may need accelerator support. Verify Python-version compatibility before committing to Python 3.14. | [recognition-engines](../../recognition-engines/SKILL.md) |
| OpenAI or OpenAI-compatible transcription API | `python -m pip install "SpeechRecognition[openai]"` | `openai`, `httpx` | OpenAI SDK authentication for hosted OpenAI, or custom base URL plus endpoint-appropriate authentication for a compatible self-hosted endpoint. | [recognition-engines](../../recognition-engines/SKILL.md) |
| Groq Whisper API | `python -m pip install "SpeechRecognition[groq]"` | `groq`, `httpx` | Groq SDK authentication and network access. | [recognition-engines](../../recognition-engines/SKILL.md) |
| Cohere Transcribe API | `python -m pip install "SpeechRecognition[cohere-api]"` | `cohere` | Cohere SDK authentication, network access, and an explicit language argument at recognition time. | [recognition-engines](../../recognition-engines/SKILL.md) |
| AssemblyAI legacy API method | `python -m pip install "SpeechRecognition[assemblyai]"` | `requests` | AssemblyAI authentication argument and network access. | [recognition-engines](../../recognition-engines/SKILL.md) |
| Silence-aware audio splitting | `python -m pip install "SpeechRecognition[audio-split]"` | `librosa`, `numpy` | Used only for `AudioData.split(..., silence_aware=True)`. | [audio-data](../../audio-data/SKILL.md) |
| Repository development | `python -m pip install "SpeechRecognition[dev]"` | `pytest`, `pytest_randomly`, `respx`, `numpy`, `pytest_httpserver`, `mypy` | Maintainer test/lint/typecheck workflow, not needed for package use. | [repo-development](../../repo-development/SKILL.md) |

## Non-extra CLI support dependency

The 3.17.0 CLI imports `tqdm` at module import time, but `tqdm` is not declared
by the base dependency list or the official extras above. If `sprc --help` or
`python -m speech_recognition.cli --help` raises `ModuleNotFoundError: No module
named 'tqdm'`, install it explicitly:

```bash
python -m pip install tqdm
```

This pitfall affects CLI inspection and Vosk model download. The base Python API
can still be installed and used for non-CLI tasks without `tqdm`.

## Common targeted install recipes

Prefer narrow recipes matched to the user's workflow:

```bash
# Base library and safe environment checks.
python -m pip install SpeechRecognition

# CLI help and Vosk model setup for offline Vosk recognition.
python -m pip install "SpeechRecognition[vosk]" tqdm
sprc download vosk

# Microphone capture demo and scripts.
python -m pip install "SpeechRecognition[audio]"

# Local Whisper file recognition on a Python version known to support it.
python -m pip install "SpeechRecognition[whisper-local]"

# OpenAI-compatible transcription API with audio chunking support.
python -m pip install "SpeechRecognition[openai,audio-split]"
```

Use shell quotes around extras, especially in shells that treat square brackets
as glob syntax.

## CI-derived compatibility notes

The repository's test workflow validates a base install on Python 3.11 and tests
many extras on Linux and Windows. Its all-extras Linux matrix includes Python
3.10 through 3.14, but the Python 3.14 install step deliberately omits local
Whisper/Faster-Whisper and audio-split groups. The project metadata also notes
that `openai-whisper` does not support Python 3.14 yet. For local Whisper work,
choose Python 3.10-3.13 unless you have independently verified the upstream
stack.

The extra-contract CI job validates each extra separately where possible,
including `assemblyai`, and sets up a Vosk model only for Vosk-specific tests.
Treat optional extras as workflow-specific capabilities rather than a mandatory
single environment.

## What the environment checker verifies

`scripts/check_speech_recognition_env.py` checks:

- Python version and `SpeechRecognition` distribution metadata;
- importability of `speech_recognition`;
- recognizer method names attached to `Recognizer`;
- `sprc` and module CLI help without running downloads;
- the presence or absence of the installed package's Vosk model directory; and
- optional dependency modules grouped by extra.

It does not download Vosk models, import authentication, call cloud services, test
microphone hardware, or load Whisper model weights.
