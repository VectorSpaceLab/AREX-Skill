# Testing Matrix

## Purpose

Use this matrix to choose focused, CI-aligned checks after repository edits. For automated suggestions, run the bundled helper:

```bash
# from the generated speech-recognition skill root
python sub-skills/repo-development/scripts/select_tests.py <changed-paths...>
```

The helper prints commands only; it never executes tests.

## Local Baseline Checks

| Check | Command | Use when | Notes |
| --- | --- | --- | --- |
| Unit test discovery | `python -m unittest discover --verbose` | Broad local sanity check after core changes. | Matches contributor docs; may skip optional service tests unless environment variables or extras are present. |
| Pytest base tests | `pytest -s -v tests/` | Reproduce base CI job after ordinary package edits. | Base CI installs `.[dev]` and runs this on Python 3.11. |
| Lint | `make lint` | Python style, doctest lint, workflow parity. | Makefile uses `pipx run flake8 --ignore=E501,E701,W503 --extend-exclude .venv,venv,build --doctests .`. |
| RST check | `make rstcheck` | `README.rst`, `CONTRIBUTING.rst`, or `reference/*.rst` changed. | Uses plain rstcheck for top-level docs and Sphinx-aware rstcheck for `reference/*.rst`. |
| Type check | `make typecheck` | Recognizer modules, tests, type-sensitive refactors. | Runs `mypy --ignore-missing-imports speech_recognition/recognizers tests`; CI installs many extras and host packages first. |
| Distribution check | `make distribute` | Packaging metadata, MANIFEST, licenses, version, entry points, package data, release-adjacent changes. | Safe build plus Twine check; does not upload. |

## Test Split by Source Area

| Changed area | Focused command(s) | Add extras/host prerequisites when |
| --- | --- | --- |
| `speech_recognition/__init__.py` | `pytest -s -v tests/test_recognition.py tests/test_special_features.py` plus affected recognizer tests. | PocketSphinx assertions need `pocketsphinx`; legacy web-service checks need explicit service access. |
| `speech_recognition/audio.py` | `pytest -s -v tests/test_audio.py` | `AudioData.split(..., silence_aware=True)` paths need `audio-split`; FLAC conversion depends on bundled or system FLAC. |
| `speech_recognition/recognizers/google.py` | `pytest -s -v tests/recognizers/test_google.py` | No live Google credentials are needed for the mocked request-builder/parser tests. |
| `speech_recognition/recognizers/google_cloud.py` | `pytest -s -v tests/recognizers/test_google_cloud.py` | Install `google-cloud` extra; tests mock client construction and credential path handling. |
| `speech_recognition/recognizers/cohere_api.py` | `pytest -s -v tests/recognizers/test_cohere_api.py` | Install `cohere-api` extra; tests mock Cohere client calls. |
| `speech_recognition/recognizers/vosk.py` or `speech_recognition/cli.py` Vosk setup | `pytest -s -v tests/recognizers/test_vosk.py` | Install `vosk` extra and set up a model with `python -m speech_recognition.cli download vosk` only when network/model download is acceptable. |
| `speech_recognition/recognizers/whisper_api/openai.py` | `pytest -s -v tests/recognizers/whisper_api/test_openai.py tests/recognizers/whisper_api/test_openai_compatible.py` | Install `openai` extra; tests use mocked HTTP/fake endpoint behavior. |
| `speech_recognition/recognizers/whisper_api/groq.py` | `pytest -s -v tests/recognizers/whisper_api/test_groq.py` | Install `groq` extra; tests use mocked HTTP behavior. |
| `speech_recognition/recognizers/whisper_local/whisper.py` | `pytest -s -v tests/recognizers/whisper_local/test_whisper.py` | Install `whisper-local`; tests skip on Python 3.14 or later. |
| `speech_recognition/recognizers/whisper_local/faster_whisper.py` | `pytest -s -v tests/recognizers/whisper_local/test_faster_whisper.py` | Install `faster-whisper`; tests skip on Python 3.14 or later. |
| `tests/test_audio.py` or audio fixtures | Run the changed test file plus `pytest -s -v tests/test_audio.py`. | Add `audio-split` when silence-aware split coverage is relevant. |
| `tests/recognizers/...` | Run the changed test file and matching source module tests. | Install the matching extra listed below. |
| RST docs | `make rstcheck` plus tests for described behavior. | Avoid release/publish side effects. |
| `pyproject.toml`, `MANIFEST.in`, `setup.py`, `SpeechRecognition.egg-info/`, `LICENSE*` | `make distribute`; add import and entry-point checks. | For FLAC/package-data edits, also run `pytest -s -v tests/test_audio.py`. |
| `.github/workflows/lint.yml` | `make lint` | Confirm action changes still call the intended local command. |
| `.github/workflows/rstcheck.yml` | `make rstcheck` | Same. |
| `.github/workflows/typecheck.yml` | `make typecheck` | Host packages may be required for audio/pocketsphinx extras. |
| `.github/workflows/unittests.yml` | Reproduce the affected CI job row below. | Match Python/platform/extras only as needed; do not force all extras locally without reason. |
| `.github/workflows/publish.yml`, `make-release.sh`, `Makefile` publish/distribute targets | `make distribute` | Publishing/uploading/tagging remains gated. |

## CI Jobs and What They Mean

### Unit tests: base

- Platform: Ubuntu.
- Python: 3.11.
- Install: create virtual environment, upgrade pip, install `.[dev]`.
- Verify: `pytest -s -v tests/`.
- Use for base package behavior that should not require optional recognizer extras.

### Unit tests: all-extras

- Platforms/Python: Ubuntu Python 3.10, 3.11, 3.12, 3.13, 3.14; Windows Python 3.11.
- Ubuntu host packages: Pulse/ALSA development headers, PortAudio development headers, and FFmpeg for Whisper.
- Windows uses an FFmpeg setup action for Whisper.
- Ubuntu Python 3.14 intentionally omits local Whisper and faster-whisper extras because openai-whisper is not supported there.
- Verify command: `pytest --doctest-modules -s -v speech_recognition/recognizers/ tests/` after Vosk model setup.
- Use for changes that may affect cross-version optional recognizer compatibility.

### Unit tests: extra-contracts

The extra-contracts job is the best evidence for each optional dependency's minimum promise:

| Extra | Install spec | Verify command |
| --- | --- | --- |
| `audio` | `.[dev,audio]` | `python -c "from speech_recognition import Microphone; Microphone.get_pyaudio()"` |
| `pocketsphinx` | `.[dev,pocketsphinx]` | `pytest -s -v tests/test_recognition.py tests/test_special_features.py` |
| `google-cloud` | `.[dev,google-cloud]` | `pytest -s -v tests/recognizers/test_google_cloud.py` |
| `whisper-local` | `.[dev,whisper-local]` | `pytest -s -v tests/recognizers/whisper_local/test_whisper.py` |
| `faster-whisper` | `.[dev,faster-whisper]` | `pytest -s -v tests/recognizers/whisper_local/test_faster_whisper.py` |
| `openai` | `.[dev,openai]` | `pytest -s -v tests/recognizers/whisper_api/test_openai.py tests/recognizers/whisper_api/test_openai_compatible.py` |
| `groq` | `.[dev,groq]` | `pytest -s -v tests/recognizers/whisper_api/test_groq.py` |
| `cohere-api` | `.[dev,cohere-api]` | `pytest -s -v tests/recognizers/test_cohere_api.py` |
| `assemblyai` | `.[dev,assemblyai]` | `python -c "from speech_recognition import Recognizer; assert hasattr(Recognizer(), 'recognize_assemblyai')"` |
| `vosk` | `.[dev,vosk]` | Set up Vosk model, then `pytest -s -v tests/recognizers/test_vosk.py` |
| `audio-split` | `.[dev,audio-split]` | `pytest -s -v tests/test_audio.py` |

## Static, RST, and Typecheck Workflows

- `.github/workflows/lint.yml` runs `make lint`.
- `.github/workflows/rstcheck.yml` runs `make rstcheck`.
- `.github/workflows/typecheck.yml` uses Python 3.12, installs audio/pocketsphinx/Google Cloud/local Whisper/faster-whisper/OpenAI/Groq/Vosk extras plus host packages, then runs `make typecheck`.

When local reproduction fails before mypy because optional packages or audio host headers are missing, decide whether the edited area requires those extras. If not, record the skip. If yes, install the smallest missing prerequisite set for that edited area.

## Publish Workflow

`.github/workflows/publish.yml` is triggered by a published release, builds with `make distribute`, and publishes with PyPI trusted publishing permissions. Local maintainer reproduction should stop at `make distribute` unless the user explicitly requests a real release upload.
