# Maintenance Guide

## Purpose

Read this when editing SpeechRecognition itself rather than using it as an application dependency. It distills maintainer-facing evidence from `CONTRIBUTING.rst`, `.devin/wiki.json`, `README.rst`, `pyproject.toml`, `MANIFEST.in`, `Makefile`, `make-release.sh`, and GitHub workflow files.

## Source Layout and Ownership

| Area | Maintainer meaning | Typical edits | First validation route |
| --- | --- | --- | --- |
| `speech_recognition/__init__.py` | Core public surface: `Recognizer`, `AudioSource`, `Microphone`, `AudioFile`, legacy recognizers, and method attachment for newer recognizer modules. | Core listening behavior, default recognizer attributes, compatibility shims, legacy web recognizers. | `tests/test_recognition.py`, affected recognizer tests, then `make typecheck` when signatures/types changed. |
| `speech_recognition/audio.py` | `AudioData`, file conversion, FLAC converter discovery, raw/WAV/AIFF/FLAC export, and split helpers. | Audio decoding/encoding, FLAC selection, byte/sample alignment, silence-aware splitting. | `tests/test_audio.py`; include `audio-split` extra checks when `silence_aware=True` behavior changed. |
| `speech_recognition/recognizers/` | Engine-specific integrations. Maintainer notes place Google, Google Cloud, PocketSphinx, Vosk, Cohere, Whisper API, and local Whisper work here. | New recognizer integrations and engine-specific bug fixes. | Matching `tests/recognizers/...` file plus extras contract from [testing matrix](testing-matrix.md). |
| `speech_recognition/cli.py` | `sprc` console script, currently including Vosk model download. | CLI argument parsing, model download behavior, progress/output handling. | CLI help/import checks plus `tests/recognizers/test_vosk.py` when Vosk setup is affected. |
| `speech_recognition/__main__.py` | Demo run by `python -m speech_recognition`; uses microphone input and Google recognition. | Demo wording or basic interactive flow. | Treat as optional-host/audio and network-facing; do not make it part of required automated checks without explicit scope. |
| `examples/` | Usage examples for microphone, files, background listening, energy calibration, special recognizer features, and audio writing. | Example updates that must match public APIs. | Syntax/import check, then nearest package tests. |
| `reference/` and `README.rst` | Public RST docs. | API reference, requirements, installation, troubleshooting, package badges. | `make rstcheck`; also run tests for any documented behavior changed. |
| `pyproject.toml`, `setup.py`, `MANIFEST.in`, `SpeechRecognition.egg-info/` | Package metadata, optional extras, entry point `sprc`, included package data, license files. | Extras, Python versions, package data, console entry points, distribution metadata. | `make distribute`, import/entry-point checks, relevant extras contract. |
| `.github/workflows/` and `Makefile` | CI contract for tests, static analysis, RST, type checking, release publishing, stale issues. | CI parity, command changes, action pin updates. | Reproduce the affected local command where safe; do not run publish. |
| `third-party/`, `LICENSE-FLAC.txt`, bundled `flac-*` binaries | FLAC source/provenance and binary license obligations. | Reproducibility, license, binary replacement, package inclusion. | `tests/test_audio.py`, package-data inspection, `make distribute`; rebuild only with explicit provenance task. |

## Recognizer Module Ownership

- Put new engine-specific implementation under `speech_recognition/recognizers/` unless the change intentionally affects the historical monolithic public surface in `speech_recognition/__init__.py`.
- Keep public `Recognizer` method availability in sync. The package attaches module recognizers near the end of `speech_recognition/__init__.py`; tests such as `test_recognizer_attributes` guard public method presence.
- Add or update an engine test under `tests/recognizers/` for module recognizers. Prefer mocked clients or local fixtures over live service calls.
- For recognizers that require a package extra, update `pyproject.toml` optional dependencies and the `extra-contracts` CI matrix together. Do not document a recognizer as supported unless its install extra and test route are explicit.
- For credentialed services, tests should use mocks, local fake servers, or skipped legacy checks unless the maintainer explicitly provides service access. Never hard-code secret values.

## Development Setup Contract

The documented editable install for maintainers is:

```bash
python -m pip install -e .[dev]
```

`CONTRIBUTING.rst` also names `pipx` as a prerequisite because Makefile targets invoke tools through `pipx run` for lint, RST, build, and Twine checks. When reproducing CI locally, install only the extras needed for the edited surface instead of installing every optional engine by default.

## Documentation and RST Maintenance

- `make rstcheck` validates `README.rst`, `CONTRIBUTING.rst`, and `reference/*.rst` with the same Sphinx-aware exception model used by the Makefile.
- If a code change alters public method signatures, optional dependency names, CLI behavior, supported Python versions, or troubleshooting guidance, update the corresponding RST in the same change.
- Avoid copying generated or external documentation back into source docs without review. Keep examples short enough to remain testable and consistent with public APIs.

## Packaging and MANIFEST Hazards

- `MANIFEST.in` grafts `speech_recognition` and `reference`, prunes `speech_recognition/models`, excludes `*.pyc`, and includes `README.rst`, `LICENSE.txt`, and `LICENSE-FLAC.txt`.
- `pyproject.toml` package data includes `version.txt`, four bundled FLAC binaries, and PocketSphinx data. If these names or locations change, update package data and run distribution checks.
- The console script entry point is `sprc = speech_recognition.cli:main`; CLI changes can break both `sprc ...` and `python -m speech_recognition.cli ...` style invocations.
- `speech_recognition/version.txt` is the dynamic package version source. Release preparation must keep it consistent with release notes or README version mentions.

## Release Commands Are Gated

Safe release-adjacent check:

```bash
make distribute
```

This builds distribution artifacts and runs Twine checks through the Makefile. It does not publish.

Do not run these unless the user explicitly asks for a release or publish operation and confirms required signing/upload prerequisites are available:

```bash
make publish
./make-release.sh VERSION_GOES_HERE
```

Additional release hazards:

- `make publish` requires a package index token environment variable and uploads `dist/*`.
- `./make-release.sh` builds a wheel, creates a detached GPG signature, and uploads wheel plus signature.
- `CONTRIBUTING.rst` describes signed tags after bumping `README.rst` and `speech_recognition/version.txt`; tag creation is also a gated release action.
- The GitHub publish workflow runs on published releases, uses `make distribute`, and publishes with PyPI trusted publishing permissions.

## FLAC Binary Provenance

SpeechRecognition bundles FLAC executables for supported platforms so users usually do not need a system `flac` binary on common Windows, Intel macOS, or x86 Linux systems. Maintenance implications:

- `flac-win32.exe` is documented as the official FLAC 1.3.2 32-bit Windows binary.
- `flac-linux-x86` and `flac-linux-x86_64` are documented as static builds from FLAC 1.3.2 source using Manylinux images; the intended rebuild is bit-for-bit reproducible.
- `flac-mac` is documented as extracted from xACT 2.39's bundled FLAC encoder.
- `third-party/flac-1.3.2.tar.xz` is provenance material, and `LICENSE-FLAC.txt` carries GPLv2 terms for the FLAC binaries.
- `AudioData.get_flac_data()` and `AudioFile` FLAC reading depend on `get_flac_converter()` in `speech_recognition/audio.py`; run audio tests after any converter selection or binary packaging edit.
- Rebuilding bundled binaries requires Docker/system package operations and must not be performed as a default test step.

## AI-Generated Contribution Caution

The contribution policy permits AI as a learning or development aid, but submitters must understand and explain their code. Reject or revise changes that show unreviewed AI generation signs: unnecessary code, inconsistent style, nonexistent API usage, broad rewrites unrelated to the issue, or docs that claim unsupported behavior.
