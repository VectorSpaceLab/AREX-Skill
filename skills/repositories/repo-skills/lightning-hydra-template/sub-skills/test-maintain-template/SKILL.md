---
name: test-maintain-template
description: "Maintain Lightning-Hydra-Template tests, CI, Makefile targets,
  package metadata, smoke profiles, RunIf skips, and package renames."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Test and Maintain the Template

Use this sub-skill when the task is about repository maintenance rather than model training itself.

## Triggers

Read this sub-skill for tasks about:

- Choosing pytest commands, no-network smoke tests, slow tests, GPU tests, or sweep tests.
- `tests/conftest.py`, `tests/test_configs.py`, `tests/test_train.py`, `tests/test_eval.py`, `tests/test_sweeps.py`, or `tests/helpers/RunIf`.
- `make test`, `make test-full`, `make format`, `pre-commit`, and GitHub Actions.
- Updating `setup.py`, console scripts, imports, coverage paths, and config targets after renaming the default `src` package.
- CI failures from missing optional dependencies, Hydra global state, strict markers, or data downloads.

## Quick workflow

1. Classify tests before running them:
   ```bash
   python <this-skill>/sub-skills/test-maintain-template/scripts/select_smoke_tests.py --profile offline
   python <this-skill>/sub-skills/test-maintain-template/scripts/select_smoke_tests.py --profile full
   ```
2. For a required no-training smoke, run:
   ```bash
   pytest tests/test_configs.py -q
   ```
3. Do not assume `make test` is no-network. It expands to `pytest -k "not slow"`, and the non-slow fast-dev training test can still download MNIST.
4. When renaming packages or moving entry files, read [package renaming](references/package-renaming.md) and run the target checker from [customize-data-model](../customize-data-model/SKILL.md).
5. For CI, keep optional GPU/sweep/logger tests guarded by `RunIf` or separate profiles.

## Read references

- [Testing and CI reference](references/testing-ci-reference.md): pytest fixtures, native test classification, Makefile targets, CI matrix, and safe command profiles.
- [Package renaming](references/package-renaming.md): update checklist for `src` package renames and setup/coverage/config targets.
- [Troubleshooting](references/troubleshooting.md): Hydra state, MNIST downloads, optional skips, strict markers, `sh`, logger credentials, and CI surprises.

## Bundled script

- [scripts/select_smoke_tests.py](scripts/select_smoke_tests.py): prints recommended pytest commands and risk notes for offline, quick, full, gpu, sweep, and rename profiles.

## Boundaries

- For Hydra config content and sweeps as experiment design, use [configure-experiments](../configure-experiments/SKILL.md).
- For train/eval semantics and checkpoints, use [train-evaluate](../train-evaluate/SKILL.md).
- For data/model implementation and `_target_` import checks, use [customize-data-model](../customize-data-model/SKILL.md).
