# Maintenance workflows

This reference helps future agents choose scoped repository-development commands for LightlySSL. Commands are meant to be run from the root of a Lightly checkout unless a command explicitly changes directory. They mirror the project Makefile and CI behavior while avoiding release or credentialed operations.

## Environment setup

For ordinary package use:

```bash
python -m pip install lightly
```

For optional public package branches:

```bash
python -m pip install "lightly[timm]"   # TIMM / MAE / ViT-style optional modules
python -m pip install "lightly[video]"  # video datasets requiring PyAV
```

For repository development, Lightly uses `uv` and a local virtual environment:

```bash
uv venv
source .venv/bin/activate
make install-dev
```

`make install-dev` installs the editable package with all extras plus development tooling and installs pre-commit hooks. If an existing environment has stale dependencies, reset it first:

```bash
make reset-venv
source .venv/bin/activate
make install-dev
```

Avoid Python 3.13 for repository-development checks unless the user has already confirmed compatible PyTorch wheels. The maintained CI matrix uses older and current supported Python versions rather than 3.13.

## Makefile command inventory

| Command | Use when | Notes |
|---|---|---|
| `make format` | The user wants automatic formatting fixes. | Runs Ruff import fixing and formatting over `benchmarks docs examples lightly tests`. |
| `make format-check` | Checking formatting without changing files. | Runs Ruff import check and format check. |
| `make lint` | Linting both package and tests. | Expands to `lint-lightly` and `lint-tests`. |
| `make lint-lightly` | Only package source needs linting. | Runs `ruff check lightly`. |
| `make lint-tests` | Only tests need linting. | Runs `ruff check tests`. |
| `make type-check` | Type-checking package and tests. | Runs `mypy lightly tests`; some modules are intentionally excluded in config. |
| `make static-checks` | Pre-test static gate. | Runs `format-check` and `type-check`. |
| `make test-fast` | Fast local unit suite. | Runs `pytest tests`; slow tests are skipped unless explicitly enabled. |
| `make test` | Full unit suite including slow tests. | Runs `pytest tests --runslow`. |
| `make test-distributed` | DDP-marked tests on the gloo pool. | Runs `USE_PYTEST_POOL=1 python -m pytest tests --runslow -m DDP`. |
| `make all-checks` | Broad pre-PR confidence. | Runs `static-checks` and the full `make test` suite. |
| `make generate-example-notebooks` | Example scripts changed. | Regenerates tracked notebooks from all example families. |

Do not use cleanup, uninstall, build, deploy, notification, or PyPI release commands as default validation steps. Treat release/publishing workflows as maintainer-owned and credential-bound.

## Changed-path command selection

Start scoped, then escalate if the change crosses multiple surfaces or the user asks for pre-PR confidence.

| Changed area | First scoped checks | Add when needed |
|---|---|---|
| `lightly/utils/benchmarking` or `tests/utils/benchmarking` | `python -m pytest tests/utils/benchmarking -q`; `make format-check` | `make type-check`; `make test-fast` if shared Lightning behavior changed. |
| `lightly/loss` or loss tests | `python -m pytest tests/loss -q`; `make format-check` | Representative model/transform tests if loss shape assumptions changed. |
| `lightly/transforms` or transform tests | `python -m pytest tests/transforms -q`; `make format-check` | Data/collate tests if outputs feed collate functions. |
| `lightly/models` or model-module tests | `python -m pytest tests/models -q`; `make format-check` | Optional `lightly[timm]` checks only if TIMM-backed modules changed. |
| `lightly/data` | `python -m pytest tests/data -q`; `make format-check` | Video tests only when `lightly[video]` / PyAV is installed and the task targets video. |
| `lightly/cli`, CLI config, or `lightly/core.py` | `python -m pytest tests/cli -q`; `make format-check` | Route command construction/data-layout details to `cli-data-embedding`; run artifact-writing CLIs only with explicit paths/budget. |
| `lightly/embedding` | `python -m pytest tests/embedding -q`; `make format-check` | CLI embed checks only when bounded by the user. |
| General package source | Most relevant targeted pytest subtree; `make static-checks` | `make test-fast`, then `make test` for broad confidence. |
| Tests only | `python -m pytest <changed test files> -q`; `make lint-tests` | Add `--runslow` if the changed tests are slow-marked. |
| DDP or distributed tests | `USE_PYTEST_POOL=1 python -m pytest tests --runslow -m DDP` | Keep this separate from ordinary `pytest`; `python -m pytest` is required for spawned workers. |
| `examples/` scripts | `make generate-example-notebooks`; `make format-check` | Inspect notebook diffs and commit regenerated notebooks. Do not run long training examples by default. |
| `docs/source` | `make format-check`; `cd docs && make html-noplot` | Occasionally `cd docs && make clean-html-noplot` for a warning-clean rebuild. |
| `benchmarks/` | `make format-check`; benchmarking utility tests if helper code changed | Full ImageNet-scale benchmarks require explicit dataset, hardware, runtime, and output policy. |
| `pyproject.toml`, package metadata, dependency files, CI workflows, or Makefile | `make static-checks`; `make test-fast` | CI-parity dependency variants such as minimal/pinned/latest installs only in disposable environments. |

The bundled command planner can generate a safe starting plan from changed paths:

```bash
python scripts/check_repo_dev_commands.py lightly/utils/benchmarking/knn.py tests/utils/benchmarking/test_knn.py
python scripts/check_repo_dev_commands.py --ci-parity pyproject.toml .github/workflows/test_minimal_deps.yml
```

It prints commands and explanations only; it does not execute checks.

## Slow tests and DDP tests

- `make test-fast` runs `pytest tests` and does not enable the repository's slow-test option.
- `make test` runs `pytest tests --runslow` and includes slow tests.
- DDP-marked tests are not part of ordinary local smoke checks. Use the dedicated command:

```bash
USE_PYTEST_POOL=1 python -m pytest tests --runslow -m DDP
```

Use `python -m pytest` rather than bare `pytest` for this command because spawned pool workers must import the tests package consistently.

## Notebook generation workflow

When Python example scripts change, regenerated notebooks are tracked and must be included with the change.

```bash
make generate-example-notebooks
git diff -- examples/notebooks
```

The generator uses Jupytext and deterministic cell ids. Stale notebooks appear as diffs after regeneration. Do not hand-edit generated notebooks as the primary fix; update the source example script and regenerate.

## Documentation checks

For documentation changes, use the no-plot HTML build first:

```bash
cd docs && make html-noplot
```

If cached builds hide warnings, use the clean no-plot build:

```bash
cd docs && make clean-html-noplot
```

The full plotting/tutorial build is usually unnecessary for ordinary PR checks and may run Python tutorial code. Use it only with an explicit runtime and dependency budget.

## CI and dependency variants

CI covers several views of the project:

- Format/type workflow: static checks on supported Python versions.
- Unit-test workflow: pinned extras and full `--runslow` pytest on supported Python versions.
- Distributed workflow: DDP-marked tests with the gloo pool enabled.
- Minimal-dependency workflow: lowest-direct dependency variants with and without extras.
- Setup workflow: package installation and CLI sanity checks.
- Notebook workflow: regenerates example notebooks and fails if tracked notebooks changed.
- Weekly dependency workflow: latest compatible dependency installation plus full tests.
- Release workflow: builds and publishes package artifacts; this is not a default contributor action.

Local CI-parity commands can be expensive and may reinstall dependencies. Run them in a disposable virtual environment:

```bash
make install-minimal
make install-minimal-extras
make install-pinned
make install-pinned-extras
make install-latest
```

Choose these only when the task changed dependency bounds, optional extras, Python-version compatibility, CI setup, or packaging metadata.

## Contributor and PR constraints

- Work on a feature branch based on `upstream/master`; do not develop directly on `master`.
- Keep changes focused to the requested package area; avoid unrelated refactors.
- Public functions and modules should use Google-style docstrings where required by the configured Ruff pydocstyle rules.
- Use full type hints and Python 3.10-style union syntax (`str | Path`) with `from __future__ import annotations` when needed for compatibility.
- Prefer keyword arguments when calling functions with more than one argument.
- Import functions through their module and classes directly from their class module.
- Before PR handoff, prefer `make format` followed by `make all-checks` when time allows; otherwise report exactly which scoped checks were run and which were intentionally skipped.
