# Repository Development Troubleshooting

## Purpose

Use this when maintainer checks fail, skip unexpectedly, or ask for optional tools, host libraries, service access, model downloads, release authentication, or contribution review fixes.

## Optional Tests Are Skipped

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `pytest.importorskip("pocketsphinx")` skips tests. | `pocketsphinx` extra is not installed. | Install `SpeechRecognition[pocketsphinx]` for the pocketsphinx contract, then rerun `tests/test_recognition.py` and `tests/test_special_features.py`. Windows skips some Sphinx assertions by design. |
| Whisper local tests skip on Python 3.14 or later. | `openai-whisper` does not support that Python version in the CI contract. | Do not treat as a failure for Python 3.14. Reproduce local Whisper on Python 3.10-3.13 when that capability is required. |
| `tests/test_audio.py` silence-aware tests skip. | Functional `numpy`/`librosa` path is missing or fails during initialization. | Install `SpeechRecognition[audio-split]` when editing `AudioData.split(..., silence_aware=True)`. If the edit is unrelated to silence-aware splitting, record the skip. |
| Vosk tests fail with missing model path. | `speech_recognition/models/vosk` was not prepared. | Run `python -m speech_recognition.cli download vosk` only if network/model download is acceptable, then rerun `tests/recognizers/test_vosk.py`. |
| Legacy web-service tests show skip reasons for Wit.ai, Houndify, or IBM. | These tests require explicit external service access. | Prefer mocked tests for new changes. Do not insert placeholder secret values; run live service checks only when the maintainer intentionally provides access. |
| Google Cloud, OpenAI, Groq, or Cohere tests skip. | Matching Python extra is missing. | Install the matching extra from [testing matrix](testing-matrix.md). The current tests are designed around mocks/fake servers, not live paid calls. |

## External Service and Credentialed Checks

- Treat any check that would call a real speech service as optional unless the task explicitly requires live integration verification.
- Never hard-code tokens, account files, or private values in tests, docs, examples, or commit messages.
- For Google Cloud code, test credential path plumbing with mocks unless live application-default credentials are explicitly part of the task.
- For OpenAI-compatible endpoints, prefer local fake server tests like the existing compatible API test instead of relying on a real endpoint.
- If a user asks for release or publish validation, verify that the request is truly about publishing before touching upload tokens, signed tags, or PyPI/GitHub release flows.

## pipx, Tool, and Makefile Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `make lint`, `make rstcheck`, or `make distribute` fails with `pipx: command not found`. | Contributor docs require pipx; Makefile invokes `pipx run`. | Install pipx using the platform's standard instructions, then rerun the Makefile target. If tool installation is out of scope, run only lower-level checks that are already available and record the gap. |
| `make typecheck` fails with `mypy: command not found`. | Dev dependencies are not installed in the active environment. | Run `python -m pip install -e .[dev]`, then install extras required by the typecheck surface. |
| Flake8 reports long-line or multi-statement differences unexpectedly. | The Makefile intentionally ignores `E501`, `E701`, and `W503`. | Reproduce with `make lint` or match its ignore flags before changing style broadly. |
| RST check fails on Sphinx roles/directives. | Top-level and `reference/*.rst` files use different rstcheck modes. | Use `make rstcheck` so `reference/*.rst` is checked with the Sphinx-aware extra and configured ignored directives. |

## PyAudio and Host Audio Dependencies

- `Microphone` requires PyAudio. If `Microphone.get_pyaudio()` raises an import or version error, install the `audio` extra and host PortAudio development files appropriate for the platform.
- Ubuntu CI installs PortAudio development headers for PyAudio and Pulse/ALSA development headers for pocketsphinx-related builds.
- Microphone examples may also depend on real input devices. Do not require hardware microphone tests for unrelated source edits.
- If a test or demo hangs around microphone input, switch to file-based `AudioFile` tests or mocked audio streams unless the task explicitly targets microphone behavior.

## FLAC and Audio Conversion Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OSError` says FLAC conversion utility is unavailable. | The platform is not covered by bundled FLAC binaries and no system `flac` command is on PATH. | Install a system FLAC command for that platform or narrow the test to formats that do not require FLAC conversion. |
| FLAC audio tests fail after packaging edits. | Bundled binary names, package data, executable bits, or MANIFEST entries changed. | Check `pyproject.toml` package data, `MANIFEST.in`, and `speech_recognition/audio.py` converter selection; then rerun `tests/test_audio.py` and `make distribute`. |
| A requested FLAC binary rebuild needs Docker. | Provenance rebuild steps are system-level and not part of default tests. | Ask for explicit provenance/rebuild authorization and preserve the documented source/version/license chain. |

## Release and Publish Blocks

- `make distribute` is the safe release-adjacent check.
- `make publish`, signed tag creation, upload commands, and `./make-release.sh VERSION` are not test commands. They require explicit release authorization.
- If publishing fails because an upload token, trusted publisher configuration, or GPG signing setup is absent, stop and report the missing prerequisite. Do not create substitute credentials or switch package indexes without instruction.
- Clean or inspect `dist/` before release packaging only when the user authorizes workspace mutation; otherwise report that old artifacts may affect Twine checks.

## AI-Generated Contribution Rejection Signals

The contribution policy warns that unreviewed AI-generated submissions can be rejected. Before handing off a patch:

- Remove unnecessary rewrites and unrelated formatting churn.
- Verify every API, option, import path, and exception name against source or tests.
- Keep style consistent with nearby files, including older compact idioms where they are intentional.
- Explain why each changed file is necessary and which focused checks cover it.
- Prefer small, test-backed changes over speculative broad refactors.
