---
name: data-preparation
description: "Routes VITS dataset preparation, filelist cleaning, and
  monotonic-alignment build tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data preparation

Use this route for custom corpus setup, filelist cleaning, and build-time prerequisites that must happen before training or inference.

## Use this route when

- You need to clean raw text filelists into the repo's `.cleaned` format.
- You need to match the LJ Speech or VCTK filelist layouts.
- You need to verify dataset sampling rates or speaker-id columns.
- You need to build the monotonic-alignment extension before importing `models`.
- You need to diagnose `phonemizer`, `espeak`, or filelist parsing issues.

## Do not use this route when

- You are actually launching training; use `training`.
- You are generating audio from a checkpoint; use `inference`.
- You only need a quick environment check; use `../../scripts/check_install.py` from the root skill.

## Read first

- `../../references/configuration.md` for the filelist formats and config-field mapping.
- `../../references/workflows.md` for the data-preparation command flow.
- `../../references/troubleshooting.md` for cross-cutting failures.
- `references/troubleshooting.md` in this sub-skill for filelist- and cleaner-specific failures.

## Bundled helpers

- `../../scripts/preprocess_text.py` — clean one or more filelists.
- `../../scripts/build_monotonic_align.py` — build the nested extension layout expected by `monotonic_align`.
- `../../scripts/check_install.py` — confirm the repo imports before you move to training or inference.

## Common workflow

1. Confirm the dataset layout and audio sampling rate.
2. Decide whether the repo's provided cleaned filelists are already enough.
3. Run `../../scripts/preprocess_text.py` only for custom raw filelists.
4. Build `monotonic_align` with `../../scripts/build_monotonic_align.py` before any model import.
5. Re-run `../../scripts/check_install.py` when the data or build step changes.

## Ownership boundaries

- Include text normalization, filelist column mapping, and dataset-layout validation here.
- Exclude training launch, checkpoints, and synthesis outputs; route those to sibling sub-skills.
