# Maintainer Workflows

This reference is for editing and validating the NeMo Speech repository, not for end-user ASR/TTS/audio/SpeechLM2 usage. It distills the repo-maintainer instructions from `AGENTS.md`, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, docs install guidance, package metadata, tests, core utilities, and CI workflows into self-contained operating rules.

## Repository Scope

- NeMo Speech focuses on speech AI collections: ASR, TTS, audio processing, SpeechLM2, speaker workflows, and shared common/core utilities.
- Active source domains are semi-isolated under `nemo/collections/*`, with shared infrastructure in `nemo/core`, `nemo/utils`, and `nemo/lightning`.
- Configuration is Hydra/OmegaConf based; training orchestration uses PyTorch Lightning; audio data loading commonly uses Lhotse.
- Megatron, Megatron Core, and Transformer Engine are not general repo assumptions for this Speech checkout. Parallelism is PyTorch-native: DDP, FSDP2, TP/SP via DTensor, and workflow-specific optional backends.
- Package evidence verified `nemo-toolkit` version `3.1.0+8f85359` from editable source-backed code. Package metadata requires Python `>=3.10`, while current docs target Python 3.12+, PyTorch 2.7+, and GPU/CUDA for training.

## Edit Policy

1. Identify the owning collection or shared layer before editing.
2. Keep fixes surgical; do not reformat untouched files or broaden behavior without a test-backed reason.
3. For user-visible classes/functions, keep docstrings and type hints aligned with contribution guidance.
4. Avoid wildcard imports unless the imported module defines `__all__` and the local style already uses that pattern.
5. Prefer `from nemo.utils import logging` over ad-hoc `print` in repo code.
6. Use explicit exceptions for runtime validation instead of `assert` in production code.
7. Avoid calling private helpers from outside their defining module unless existing code establishes that contract.
8. Add or update `__init__.py` exports only when the public import surface intentionally changes.

## Bug-Fix Flow

NeMo maintainer instructions require reproduction before repair:

1. Reproduce the issue with the smallest failing case you can isolate.
2. Add that reproduction as a focused unit test near the affected collection or shared module.
3. Apply the source fix.
4. Run the new test, then the smallest relevant neighboring suite.
5. Run formatting checks on touched Python files.

For an ASR bug, for example, place the regression in `tests/collections/asr/...`, run it with `-m "not pleasefixme"`, then consider the adjacent ASR test directory if the fix touches shared decoding, dataset, or model behavior. For shared infrastructure, prefer `tests/core`, `tests/utils`, `tests/hydra`, or `tests/lightning` as appropriate.

## Collection Boundaries

- ASR model selection, `.nemo`/pretrained loading, transcription, timestamps, streaming, fine-tuning, decoding, ASR manifests, WER/BLEU, and ASR Lhotse batching route to `../asr/SKILL.md`.
- Audio-to-audio enhancement, restoration, separation, generation, multi-channel handling, and audio metrics route to `../audio/SKILL.md`.
- SpeechLM2/SALM/SALMAutomodel, duplex STT/S2S/EAR-TTS, Nemotron VoiceChat, HF export, vLLM plugin, and voice-agent work route to `../speechlm2/SKILL.md`.
- Speaker recognition, diarization, VAD, forced alignment, RTTM/CTM/UEM, and ASR+diarization scoring route to `../speaker-diarization/SKILL.md`.
- Generic repo installation, dependency selection, tests, formatting, docs, CI labels, and source-tree maintenance stay in this sub-skill.

## Install Choices for Maintainers

Choose the smallest environment that can validate the change:

- Source/developer baseline: `uv sync --extra all --extra cu13` for the actively tested source workflow. Add `--group test` only when running the test suite and `--group docs` only when building docs.
- Exact supported stack: add `--locked --python 3.13` when reproducing the container/CI baseline.
- CUDA choice: on Linux, pick exactly one of `--extra cu13` or `--extra cu12`. Do not request both.
- Bring-your-own stack: create or activate an environment with Python 3.12+ and a compatible PyTorch build, then install NeMo with `uv pip install 'nemo-toolkit[asr,tts]'` or the minimal collection extras needed. Do not use `uv sync --locked` for bring-your-own PyTorch because it applies the lockfile baseline and may replace the existing stack.
- Docs-only work: install docs dependencies with `uv sync --locked --group docs` or the equivalent prepared environment, then use docs build commands from `references/testing-and-formatting.md`.

## Docs Workflow

- Docs source is Sphinx-based under `docs/source` and builds into `docs/build/html`.
- For content-only docs edits, run an incremental build: `uv run make -C docs html`.
- For structural docs changes, run a clean build: `uv run make -C docs clean html`.
- For link changes, run `uv run make -C docs clean linkcheck` and then the bundled repo link-check script only if you are intentionally validating external links in a prepared checkout.
- Prefer Sphinx `:ref:` labels for internal references when possible; this avoids fragile HTML-heading links and false positives.

## CI and PR Guidance

- Feature branches should target `main`. Community contributors generally use fork-based PRs.
- PRs should do one thing and include relevant focused unit tests.
- Commits may need sign-off or signature depending on contributor policy; follow the project’s current PR requirements.
- GitHub Actions CI is triggered by the `Run CICD` label in the current workflow guidance. Re-run by removing and re-adding that label or by using the project’s trusted-bot process when needed.
- Use `Run e2e nightly` only when a PR truly needs nightly end-to-end coverage, and pair it with `Run CICD`.
- `skip-linting` and `skip-docs` labels bypass those checks but should be exceptional, not a default workaround.
- Formatting CI may auto-commit Black/isort fixes back to a PR branch.
- `.github/workflows/**` is evidence for CI behavior, not a safe edit target. Do not modify workflow files unless the user explicitly asks.

## Source Scripts and Native Artifacts

This sub-skill bundles only `scripts/select_tests.py` because it is deterministic, local, and no-execution by design. Other repo scripts are reference-only for maintainer workflows:

- Training, inference, checkpoint, and conversion examples are often GPU-heavy, network/model-download dependent, or mutate outputs/checkpoints.
- Dataset preparation scripts may shard, rewrite, or create large files.
- Test shell wrappers under functional tests encode CI-like environments but may run large CPU/GPU suites and set environment variables for CI.
- CI workflows are not runtime helpers; treat them as evidence for labels and validation categories.

When a native test or example is useful for verification, first classify it for safety: local-only, no downloads, bounded runtime, no training, no destructive writes, and no hidden credentials. Run help-only or dry-run checks before any expensive command.

## Forbidden Operations

- Do not push to `main` or create commits/branches unless the user explicitly asks.
- Do not modify `.github/workflows/**` unless explicitly requested.
- Do not delete tests unless explicitly requested.
- Do not run network/model-download, training, benchmark, checkpoint-mutating, or destructive data commands as routine validation.
- Do not install broad extras or compiled backends just to validate a small CPU-safe change.
