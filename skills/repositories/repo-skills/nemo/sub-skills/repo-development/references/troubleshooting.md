# Troubleshooting Repo Development

Use this reference to diagnose maintainer workflow failures before broadening installs or running expensive native suites.

## Install or Import Failures

Symptoms:

- `import nemo` works but `import nemo.collections.<collection>` fails.
- A collection import raises missing dependency errors for Lhotse, librosa, soundfile, sentencepiece, text processing, Automodel, vLLM, or audio libraries.
- `uv sync` resolves an unexpected PyTorch/CUDA build.
- Tests fail during collection import before reaching the changed code.

Actions:

1. Confirm whether the task needs a collection extra (`asr`, `tts`, `audio`, `speechlm2`, or `all`) or only base/shared code.
2. Confirm whether the active workflow is source `uv sync` or bring-your-own `uv pip`/`pip`.
3. For source uv installs, pick exactly one CUDA extra on Linux: `cu13` or `cu12`.
4. For bring-your-own environments, install PyTorch first and then use `uv pip install 'nemo-toolkit[...]'`; do not use the locked sync path.
5. If only docs/style/tests are needed, install only `--group docs` or `--group test` as appropriate.
6. Keep optional imports lazy when fixing source so unrelated collections remain importable without heavy extras.

## CPU, GPU, CUDA, and Compiled Backend Failures

Symptoms:

- GPU tests fail because CUDA is unavailable or the PyTorch build is CPU-only.
- k2, Numba, FlashAttention, Mamba, Transformer Engine, DeepEP, grouped GEMM, or vLLM imports fail.
- Tests pass on CPU but fail on GPU due to dtype, precision, distributed, or CUDA graph behavior.
- Compiled extras fail to build outside the supported container environment.

Actions:

1. Decide whether the failing behavior is truly GPU/backend-specific. If not, run the focused CPU-safe test with `--cpu`.
2. Check that PyTorch reports the expected CUDA availability and CUDA version.
3. For SpeechLM2/Automodel acceleration, remember compiled dependencies are optional; do not require them unless testing that backend specifically.
4. Prefer Docker/container reproduction for compiled extras because source builds need CUDA build tools, architecture flags, no-build-isolation, and backend-specific patches.
5. For distributed failures, minimize to a single test node or the smallest local launch pattern before attempting multi-node or e2e runs.

## Data, Config, Schema, and Manifest Mistakes

Symptoms:

- JSONL manifests fail because fields such as audio path, duration, text, speaker label, RTTM path, or target audio are absent or malformed.
- Hydra configs fail with missing keys, struct-mode errors, or invalid `_target_` values.
- Lhotse workflows fail on cut/shar manifests, durations, sampling weights, or dynamic bucketing.
- Tests fail only after trying to download or unpack test data.

Actions:

1. Route workflow-specific manifest validation to the relevant sibling sub-skill helper when available: ASR, audio, SpeechLM2, or speaker-diarization.
2. For config instantiation, prefer `nemo.core.classes.common.safe_instantiate` instead of raw `hydra.utils.instantiate`; tests enforce this pattern.
3. Keep Hydra overrides exact: use `key=value`, quote shell-sensitive values, and avoid mixing list/dict syntax without OmegaConf-compatible quoting.
4. Use `--use_local_test_data` only when the expected local test archive exists.
5. Add `--with_downloads` only when cloud model/data downloads are explicitly part of the validation.

## CLI, API, and Hydra Misuse

Symptoms:

- Example-style commands ignore overrides or write outputs to unexpected directories.
- `pl.Trainer` arguments fail after config conversion.
- `exp_manager` creates or resumes from unexpected experiment directories.
- A config `_target_` tries to instantiate an unsafe or unapproved class.

Actions:

1. Confirm the entrypoint uses the standard Hydra runner pattern and that overrides are passed after the script path.
2. Use `nemo.utils.trainer_utils.resolve_trainer_cfg` when converting trainer config dictionaries into Lightning-ready arguments.
3. Check `exp_manager` output and resume settings before running commands that create checkpoints or experiment directories.
4. For tests, run from a clean directory without valuable `lightning_logs`, `NeMo_experiments`, or `nemo_experiments` directories because test fixtures may clean them up.
5. Keep source fixes in shared config helpers covered by `tests/hydra`, `tests/core`, or `tests/utils` as appropriate.

## Test Selection Problems

Symptoms:

- A full `pytest` run is too slow, downloads data, or hits unrelated broken tests.
- Tests are deselected unexpectedly by markers.
- `pytest` fails with strict marker errors.
- Numba/CUDA compatibility checks fail in otherwise CPU-focused tests.

Actions:

1. Start with the exact new or failing test node.
2. Add `-m "not pleasefixme"` for routine validation.
3. Use `--cpu` for CPU-safe paths and `--relax_numba_compat` only when the suite’s established command uses it.
4. Use `pytest --markers` if a marker expression is unclear.
5. Use `scripts/select_tests.py` to generate a focused command plan from changed paths before broadening.

## Formatting and Docs Failures

Symptoms:

- CI formatting disagrees with local output.
- Black changes quote styles unexpectedly.
- isort moves `nemo` imports into the wrong group.
- Docs builds fail on missing references, broken toctrees, or linkcheck output.

Actions:

1. Use the project’s configured Black/isort, not default line length 88.
2. Keep Black `skip_string_normalization` behavior by running the configured project tool, not an unrelated formatter profile.
3. Check only touched Python paths first: `isort --check <paths> && black --check <paths>`.
4. For docs, run `uv run make -C docs html`; use `clean html` after structural changes.
5. Prefer Sphinx `:ref:` labels for internal links when linkcheck reports fragile heading URLs.

## CI and PR Surprises

Symptoms:

- CI does not start after a PR update.
- Lint/docs jobs are skipped or unexpectedly included.
- Nightly tests do not run despite a label change.
- Formatting changes appear as an auto-commit.

Actions:

1. Confirm the `Run CICD` label is present when a manual CI run is expected.
2. For nightly e2e, ensure `Run e2e nightly` is present before CI starts and pair it with `Run CICD`.
3. Treat `skip-linting` and `skip-docs` as maintainer exceptions.
4. Do not edit CI workflows unless the user explicitly asks; use workflow files only as evidence for current behavior.
5. If CI failure analysis requires running a broad or GPU-heavy suite locally, ask for confirmation and hardware/runtime constraints first.

## When to Stop and Ask

Ask before:

- Installing broad extras, CUDA stacks, or compiled backends in a user environment.
- Running tests with downloads, nightly/e2e, multi-GPU, training, or large checkpoint conversion.
- Mutating an existing environment to repair dependency conflicts.
- Modifying `.github/workflows/**`, deleting tests, or changing repository policy files.
- Using unsafe checkpoint loading settings on untrusted files.
