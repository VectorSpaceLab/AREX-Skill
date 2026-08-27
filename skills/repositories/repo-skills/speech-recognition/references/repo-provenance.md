# Repo Provenance

```yaml
schema: disco.repo-provenance.v1
skill_id: speech-recognition
source:
  repository: Uberi/speech_recognition
  remote_url: https://github.com/Uberi/speech_recognition.git
  vcs: git
  commit: 0a675d1e5232dbeae1be8d071c923fb37f0f163a
  branch: master
  exact_tag: null
  package_distribution: SpeechRecognition
  package_import: speech_recognition
  package_version: 3.17.0
  working_tree_state: dirty-after-generation
  dirty_state_note: Generated skill and review artifacts were written under skills/ after source evidence capture; no source-code changes were part of the evidence baseline.
  generated_at: 2026-08-13
```

## Evidence paths used

The generated skill distilled these repository-relative evidence categories:

- Package metadata: `pyproject.toml`, `setup.py`, `MANIFEST.in`.
- Core package source: `speech_recognition/__init__.py`, `speech_recognition/audio.py`, `speech_recognition/cli.py`, `speech_recognition/exceptions.py`.
- Recognizer modules: `speech_recognition/recognizers/`.
- Package data facts: `speech_recognition/version.txt`, bundled FLAC binary names, default PocketSphinx English data layout, and `speech_recognition/models/` as runtime model location.
- Public docs and examples: README, library reference, PocketSphinx notes, and example workflows for file transcription, microphone capture, background/threaded listening, special Sphinx features, and audio writing.
- Native tests: core audio tests, recognizer default tests, engine-specific mocked tests, optional Sphinx/Vosk tests, and audio split tests.
- Maintainer evidence: contributor guide, Makefile, GitHub unit/lint/typecheck/rstcheck workflows, and maintainer source-layout notes.

These evidence paths are provenance only. Runtime workflows in this skill use bundled references and scripts rather than requiring the original checkout's docs, examples, tests, or scripts to remain available.

## Refresh guidance

Refresh this skill when any of these change:

- `speech_recognition` public class signatures or recognizer method attachment.
- `AudioData`, `AudioFile`, FLAC converter, or split behavior.
- Optional extras or Python support in package metadata.
- `sprc` CLI arguments, Vosk model location, or CLI dependencies.
- Recognizer modules, provider SDK wrappers, credential conventions, return shapes, or exceptions.
- Maintainer test matrix, packaging data, release process, or contribution rules.
