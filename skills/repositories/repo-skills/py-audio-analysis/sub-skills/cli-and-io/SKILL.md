---
name: cli-and-io
description: "Use pyAudioAnalysis legacy command-line and audio I/O surfaces
  safely, including dependency probes, format handling, conversion side effects,
  and routing to API-focused workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cli-and-io

Use this sub-skill when the task is about safely invoking pyAudioAnalysis command-line behavior, checking whether an installation has the media dependencies needed for a requested audio format, or understanding side effects from conversion and plotting helpers.

## Start here

1. Check the installed package and legacy CLI shape with [`scripts/inspect_cli.py`](scripts/inspect_cli.py). It locates the installed `pyAudioAnalysis` package, compensates for legacy top-level imports, and prints subcommand help without running an analysis task.
2. Check audio I/O readiness with [`scripts/audio_io_smoke.py`](scripts/audio_io_smoke.py). It synthesizes a tiny WAV, reads it through `audioBasicIO`, and reports optional media tools such as `ffmpeg`, `avconv`, `eyed3`, and `pydub`.
3. For command selection, flags, execution patterns, and side effects, read [`references/cli-reference.md`](references/cli-reference.md).
4. For WAV/AIFF/MP3/AU/OGG behavior and conversion helpers, read [`references/audio-formats.md`](references/audio-formats.md).
5. For common failures and safe recovery patterns, read [`references/troubleshooting.md`](references/troubleshooting.md).

## Route by intent

- Stay in this sub-skill for: command construction, shell quoting, dependency probes, format support, conversion-output risk, headless plotting concerns, and legacy script invocation.
- Route feature extraction, spectrogram/chromagram computation, beat features, and visualization interpretation to the feature/visualization-focused sibling selected by the root skill.
- Route classifier or regression training and inference details to the model-training/classification-focused sibling selected by the root skill.
- Route segmentation, HMM, diarization, silence removal, and thumbnail algorithm details to the segmentation-focused sibling selected by the root skill.
- Treat maintainer shell tests that require large external datasets as reference-only signals; do not use them as direct runtime instructions.

## Guardrails

- pyAudioAnalysis 0.3.14 has no installed console-script entry point for `audioAnalysis.py`; use the legacy script execution pattern in [`references/cli-reference.md`](references/cli-reference.md) instead of assuming `pyAudioAnalysis ...` exists.
- Do not run `python -m pyAudioAnalysis.audioAnalysis` for the legacy CLI. The module uses top-level imports such as `ShortTermFeatures`, so module execution commonly raises `ModuleNotFoundError` unless the package directory itself is on `sys.path`.
- Run conversion and segmentation-writing commands only on scratch copies or explicit output locations. Several helpers write next to inputs or delete/recreate output folders.
- Expect plotting or browser-opening side effects from spectrogram/chromagram, feature visualization, diarization, thumbnailing, regression folder plots, and some model-evaluation paths.
