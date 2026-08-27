---
name: cli-model-setup
description: "Install SpeechRecognition, select optional extras, prepare
  CLI/model assets, and check runtime environments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI Model Setup

Use this sub-skill when the user asks how to install SpeechRecognition, choose
optional extras, validate an environment, use the `sprc` command, prepare the
Vosk model expected by the package, or understand the interactive module entry
points.

## Route quickly

- Package identity and install facts: distribution name `SpeechRecognition`,
  import package `speech_recognition`, console script `sprc`, Python `>=3.10`.
  See [optional dependencies](references/optional-dependencies.md).
- CLI and model setup: use [CLI reference](references/cli-reference.md) before
  running `sprc download vosk`; that command downloads from the network and
  writes into the installed package's model directory.
- Non-invasive validation: run the bundled
  [environment checker](scripts/check_speech_recognition_env.py) to inspect the
  installed version, recognizer method wiring, `sprc` help, and optional import
  groups without downloading models or checking authentication.
- Install/CLI failure diagnosis: see
  [troubleshooting](references/troubleshooting.md), especially the `tqdm` CLI
  import pitfall and Python 3.13+ compatibility-package issues.

## Boundaries

- Recognition method selection, parameters, authentication, and transcription
  behavior belong to [recognition-engines](../recognition-engines/SKILL.md).
- Audio file loading, conversion, chunking, FLAC payloads, and `AudioData`
  manipulation belong to [audio-data](../audio-data/SKILL.md).
- Microphone capture, PyAudio device selection, ambient-noise calibration, and
  `python -m speech_recognition` demo behavior belong to
  [capture-listening](../capture-listening/SKILL.md).
- Maintainer CI matrices, repository tests, lint/typecheck/rstcheck, and release
  tasks belong to [repo-development](../repo-development/SKILL.md).

## Safe operating rules

- Do not run `sprc download vosk` unless the user accepts network download,
  unzip, overwrite, and installed-package write side effects.
- Do not run `python -m speech_recognition` as an automated check; it is an
  interactive microphone demo and can block or call a network recognizer.
- Prefer targeted extras over installing every optional group. Install only the
  workflow the user needs, then verify with the bundled checker.
