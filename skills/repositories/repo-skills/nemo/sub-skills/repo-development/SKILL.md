---
name: repo-development
description: "Use for NeMo Speech repository maintenance: installs, code style,
  focused tests, docs builds, bug reproduction, optional backends, safe
  verification, and PR/CI guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Repo Development

Use this sub-skill when changing, validating, or reviewing the NeMo Speech repository itself: installing a developer environment, choosing optional dependency groups, adding/fixing tests, running formatting checks, building docs, triaging import/backend failures, planning safe native verification, and preparing PR/CI guidance.

Route end-user model work elsewhere. Classic ASR transcription/fine-tuning/decoding belongs in `../asr/SKILL.md`; audio enhancement/separation belongs in `../audio/SKILL.md`; SpeechLM2/SALM/voice-agent work belongs in `../speechlm2/SKILL.md`; speaker diarization/VAD/forced alignment belongs in `../speaker-diarization/SKILL.md`. TTS synthesis and generic data/tokenizer tools should use their sibling sub-skills when present.

## Start Here

1. Read `references/maintainer-workflows.md` for repository architecture, edit policy, bug-fix flow, docs, PR/CI, and safe source-script handling.
2. Read `references/testing-and-formatting.md` before choosing `pytest`, `isort`, `black`, docs, or native verification commands.
3. Read `references/dependency-backends.md` before installing extras, CUDA groups, docs/test groups, or optional compiled backends.
4. Read `references/troubleshooting.md` when imports, optional dependencies, CUDA/backends, manifests/configs, Hydra overrides, docs, tests, or CI fail.
5. Run `python scripts/select_tests.py --help` to plan focused commands from changed paths or capability keywords. The helper prints commands only; it never runs tests, downloads data, trains, formats, or mutates files.

## Core Rules

- Reproduce bugs first with a minimal focused test, add the reproduction as a unit test, then fix the source and verify the targeted test passes.
- Keep changes focused; do not modify CI workflow files, delete tests, push branches, or change unrelated formatting unless explicitly asked.
- Use NeMo formatting settings: 119-character lines, Black required version 24 style, `skip_string_normalization = true`, and isort `profile = black` with `nemo` as first-party.
- Prefer focused validation: run relevant tests with `-m "not pleasefixme"`, then run `isort --check` and `black --check` on touched Python paths.
- Treat original repo examples, utility scripts, and workflow files as evidence unless a safe bundled helper exists here. Long-running, network-bound, GPU/training-heavy, checkpoint-mutating, or checkout-dependent scripts are reference-only in this sub-skill.

## Safe Bundled Tool

- `scripts/select_tests.py` maps changed paths and capability keywords to focused command suggestions such as `pytest tests/collections/asr -m "not pleasefixme" -v`, `isort --check <paths>`, `black --check <paths>`, and docs build commands.
- Example: `python scripts/select_tests.py --changed nemo/collections/asr/models/foo.py tests/collections/asr/test_foo.py --keyword docs --keyword asr`.

## Evidence Base

This sub-skill distills repository evidence from `AGENTS.md`, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `docs/source/starthere/install.rst`, `docs/README.md`, `tests/**`, `nemo/core/**`, `nemo/utils/**`, and `.github/workflows/**`. Runtime guidance is self-contained; future agents should not need to reopen those source files or run original repo scripts to complete maintainer tasks.
