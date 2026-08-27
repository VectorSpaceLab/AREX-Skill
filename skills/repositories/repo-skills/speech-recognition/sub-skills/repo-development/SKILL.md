---
name: repo-development
description: "Maintainer workflow guidance for editing SpeechRecognition source,
  tests, docs, CI, release packaging, and bundled FLAC provenance safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Repo Development

Use this sub-skill when the task is to modify or review the SpeechRecognition repository itself: source edits, recognizer module ownership, focused test selection, CI parity, lint/RST/type checks, packaging data, release preparation, or bundled FLAC provenance.

Do not use this sub-skill for ordinary end-user transcription or package usage. Route audio-file workflows to `audio-data`, microphone/listening workflows to `capture-listening`, recognizer/API/model selection to `recognition-engines`, and `sprc`/model setup to `cli-model-setup`.

## Read These Bundled Files

- [Maintenance guide](references/maintenance.md) for source layout, module ownership, contribution policy, packaging, release hazards, FLAC provenance, and AI-generated contribution caution.
- [Testing matrix](references/testing-matrix.md) for local checks, CI jobs, extras contract tests, optional dependency coverage, and safe release-adjacent verification.
- [Troubleshooting](references/troubleshooting.md) for skipped optional tests, external service checks, pipx/tooling setup, PyAudio host dependencies, release authentication blocks, and review rejection signals.
- [Focused test selector](scripts/select_tests.py) to suggest commands from changed paths or workflow names without executing them.

## Operating Rules

1. Start by classifying the changed surface: core `Recognizer`/source classes, `audio.py` conversion and split logic, engine modules under `speech_recognition/recognizers/`, CLI/demo, docs/RST, packaging metadata, workflows, or release/FLAC artifacts.
2. Use the bundled [focused test selector](scripts/select_tests.py) to propose focused tests. From this sub-skill directory, run `python scripts/select_tests.py <changed-paths...>`. Add `--workflow <name>` for CI job names or extras such as `audio`, `pocketsphinx`, `vosk`, `openai`, or `publish`.
3. Prefer safe checks first: focused `pytest`, `python -m unittest discover --verbose`, `make lint`, `make rstcheck`, `make typecheck`, and `make distribute` when packaging changed.
4. Treat optional dependencies, model downloads, external service accounts, and host audio packages as explicit prerequisites. Do not turn skips into failures unless the edited capability requires that extra.
5. Never run `make publish`, `./make-release.sh`, package upload, tag signing, token use, or FLAC Docker rebuild steps by default. Require an explicit maintainer release/provenance request and verify prerequisites before any destructive or credentialed action.
6. Keep changes reviewable and explainable. The upstream contribution guidance rejects unreviewed AI-looking changes, nonexistent APIs, unnecessary rewrites, and inconsistent style.
