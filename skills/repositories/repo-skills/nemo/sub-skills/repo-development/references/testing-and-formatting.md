# Testing and Formatting

Use this reference to pick focused validation commands for repository changes. Commands are examples to run from the repository root in a prepared environment. Start narrow, then broaden only when the touched area and risk justify it.

## Style Settings

NeMo’s source style comes from `pyproject.toml` and maintainer guidance:

- Black line length: `119`.
- Black required major style version: `24`.
- Black target versions: `py310`, `py311`, `py312`, `py313`.
- Black keeps existing quote style because `skip_string_normalization = true`.
- Jupyter notebooks are excluded from automatic Black discovery; do not reformat notebooks outside the user’s requested changes.
- isort uses `profile = black`, `line_length = 119`, `py_version = 310`, `known_first_party = ["nemo"]`, and third-party grouping for `nemo_text_processing`, `examples`, and `scripts`.
- `setup.py` and `docs/source/conf.py` are skipped by isort config.

Focused checks:

```bash
isort --check path/to/file_or_dir
black --check path/to/file_or_dir
```

Focused fixes, only when formatting changes are intended:

```bash
isort path/to/file_or_dir
black path/to/file_or_dir
```

## Pytest Defaults and Markers

Project pytest settings include `--verbose --pyargs --durations=0 --strict-markers`, `testpaths = ["tests"]`, and strict marker registration. Important markers and options:

- `unit`: isolated functionality.
- `integration`: subsystem integration.
- `system`: highest integration level.
- `acceptance`: user acceptance criteria.
- `docs`: documentation-related tests.
- `skipduringci`: skipped in CI because another job covers it, but useful for user setup checks.
- `pleasefixme`: broken tests; skip with `-m "not pleasefixme"` for normal validation.
- `--cpu`: force CPU-mode tests where supported.
- `--with_downloads`: opt into tests that download models/data from cloud caches.
- `--use_local_test_data`: use local test data instead of downloading the default archive.
- `--relax_numba_compat`: relax CUDA/Numba compatibility checks in relevant suites.
- `--nightly`: opt into nightly QA tests.

Default maintainer rule: skip known-broken tests unless you are specifically fixing them.

```bash
pytest path/to/relevant_tests -m "not pleasefixme" -v
```

## Focused Test Selection

Use the bundled helper to print a safe command plan without executing it:

```bash
python scripts/select_tests.py --changed nemo/core/config/hydra_runner.py tests/hydra/test_hydra_runner.py --keyword hydra
```

Manual mapping:

- `nemo/collections/asr/**` or `tests/collections/asr/**`: `pytest tests/collections/asr -m "not pleasefixme" -v`.
- `nemo/collections/audio/**` or `tests/collections/audio/**`: `pytest tests/collections/audio -m "not pleasefixme" -v`.
- `nemo/collections/tts/**` or `tests/collections/tts/**`: `pytest tests/collections/tts -m "unit and not pleasefixme" -v` for a fast default; broaden only when needed.
- `nemo/collections/speechlm2/**` or `tests/collections/speechlm2/**`: `pytest tests/collections/speechlm2 -m "not pleasefixme" -v`.
- `nemo/collections/common/**` or shared Lhotse/data utilities: `pytest tests/collections/common -m "not pleasefixme" -v`.
- `nemo/core/**`: `pytest tests/core -m "not pleasefixme" -v` and consider `tests/core_ptl` if PyTorch Lightning integration changes.
- `nemo/utils/**`: `pytest tests/utils -m "not pleasefixme" -v` and neighboring core tests if the utility is shared by `ModelPT`, checkpointing, logging, or trainer setup.
- `nemo/lightning/**`: `pytest tests/lightning -m "not pleasefixme" -v`.
- Hydra/config runner changes: `pytest tests/hydra -m "not pleasefixme" -v`.
- Documentation-only changes: docs build commands, not collection tests by default.

For a regression test, run the exact new test first:

```bash
pytest tests/path/test_file.py::test_name -m "not pleasefixme" -v
```

Then run the smallest owning directory.

## CPU/GPU and Download Safety

- Use `--cpu` for CPU-safe unit tests when no GPU is available or when reproducing CPU behavior.
- Do not add `--with_downloads` unless model/data download is central to the issue and the user/environment permits it.
- Avoid nightly/e2e suites during routine iteration; they can be long-running and hardware-dependent.
- Functional test shell scripts under `tests/functional_tests` are useful evidence for CI-like flags, but they can run broad coverage suites and set CI-specific environment variables. Treat them as reference-only unless the user asks for a full CI-like run.
- Some tests clean up `lightning_logs`, `NeMo_experiments`, and `nemo_experiments`; avoid running tests from a directory containing valuable experiment outputs with those names.

## Docs Validation

Install docs dependencies only when the task touches docs or Sphinx configuration:

```bash
uv sync --locked --group docs
uv run make -C docs html
```

Use a clean build for structure, index, or dependency changes:

```bash
uv run make -C docs clean html
```

Use link checking only when link changes matter and network access is acceptable:

```bash
uv run make -C docs clean linkcheck
```

If Sphinx reports false positives for internal section links, prefer rewriting with explicit labels and `:ref:` instead of adding more brittle HTML links.

## Safe Native Verification Checklist

Before running a native command that is not a focused unit/style/docs check, confirm:

- It is local-only or the user approved network/model downloads.
- It does not train, benchmark, launch services, or require multi-GPU hardware unless explicitly requested.
- It does not mutate checkpoints, data shards, repository config, or CI files.
- It writes only to a caller-controlled temporary/output directory.
- It can be bounded by a specific test node, help flag, dry-run option, or small fixture.

If any item fails, document it as reference-only and suggest the closest safe preflight instead.
