# BayesianOptimization development workflows

This reference is for agents maintaining a source checkout. It is not package
runtime usage guidance.

## Install choices

### Minimal editable/runtime-oriented install

Use this when a change only needs imports and a small focused unit test:

```bash
uv sync
```

The runtime package declares `requires-python = ">=3.9"` and runtime
requirements with Python-version markers:

- `colorama>=0.4.6`
- `numpy>=1.25` for Python `<3.13`
- `numpy>=2.1.3` for Python `>=3.13,<3.14`
- `numpy>=2.3.0` for Python `>=3.14`
- `packaging>=20.0` for Python `<3.14`; `packaging>=26.0` for Python `>=3.14`
- `scikit-learn>=1.0.0` for Python `<3.14`; `scikit-learn>=1.8.0` for Python
  `>=3.14`
- `scipy>=1.0.0` for Python `<3.13`; `scipy>=1.14.1` for Python
  `>=3.13,<3.14`; `scipy>=1.17.0` for Python `>=3.14`

If a resolver proposes NumPy 1 on Python 3.13 or newer, or old SciPy/scikit-learn
on Python 3.14, treat that as an environment mismatch rather than a package
bug.

### Development install used by CI

Use this for broad testing, Ruff, notebooks, docs, and pre-commit:

```bash
uv sync --extra dev
```

The `dev` extra is intentionally broad. It includes pytest and coverage,
notebook tooling (`jupyter`, `nbconvert`, `nbformat`, `nbsphinx`), docs tooling
(Sphinx, `sphinx-immaterial`, autodoc type hints), `ruff`, `pre-commit`, and
`matplotlib`. Expect this environment to be slower to resolve and larger than a
minimal runtime install.

## Supported Python/NumPy test matrix

The test workflow covers these Python versions: 3.9, 3.10, 3.11, 3.12, 3.13,
3.14, and free-threaded 3.14 (`3.14t`). It combines them with NumPy major
versions 1 and 2, except NumPy 1 is excluded for Python 3.13 and newer.

The CI test job installs with:

```bash
uv sync --extra dev
```

Then it pins the requested NumPy family:

```bash
uv pip install "numpy>=1.25,<2" "scipy<1.18"  # NumPy 1 lane
uv pip install "numpy>=2"                     # NumPy 2 lane
```

Finally it runs:

```bash
uv run --no-sync pytest --cov-report xml --cov=bayes_opt/
```

For local maintenance, run a focused Python version first. Escalate to selected
matrix lanes when changing dependency markers, NumPy/SciPy/scikit-learn
compatibility, array semantics, random-state behavior, or free-threaded Python
compatibility.

## Focused test mapping by touched files

Use the smallest relevant set first, then expand if failures or cross-cutting
behavior appear.

| Touched files | Focused native checks |
| --- | --- |
| `bayes_opt/acquisition.py`, acquisition docs/examples | `uv run pytest tests/test_acquisition.py` |
| `bayes_opt/bayesian_optimization.py`, optimizer orchestration/state | `uv run pytest tests/test_bayesian_optimization.py` |
| `bayes_opt/constraint.py`, constrained optimization behavior | `uv run pytest tests/test_constraint.py tests/test_acquisition.py::test_integration_constrained` |
| `bayes_opt/domain_reduction.py` | `uv run pytest tests/test_seq_domain_red.py` |
| `bayes_opt/parameter.py`, typed/categorical/integer parameters, kernel wrapping | `uv run pytest tests/test_parameter.py tests/test_target_space.py` |
| `bayes_opt/target_space.py` | `uv run pytest tests/test_target_space.py tests/test_bayesian_optimization.py` |
| `bayes_opt/util.py` | `uv run pytest tests/test_util.py` |
| `bayes_opt/logger.py` | `uv run pytest tests/test_logger.py` |
| Public API/export edits in `bayes_opt/__init__.py` | `uv run pytest tests/test_bayesian_optimization.py tests/test_acquisition.py tests/test_constraint.py` |
| `examples/*.ipynb` or notebook-support dependencies | `uv run pytest tests/test_notebooks_run.py` |
| `examples/*.py` | run the relevant script manually after focused unit tests, for example `uv run python examples/sklearn_example.py` |
| `docsrc/**`, README/API docs links | `cd docsrc && uv run make html` or, for release-like docs output, `cd docsrc && uv run make github` |
| `pyproject.toml`, `uv.lock`, dependency markers, build metadata | focused unit tests plus selected CI-like Python/NumPy lanes; consider `uv build` only for package-build validation |
| `ruff.toml`, `.pre-commit-config.yaml`, formatting-only changes | Ruff format/lint checks and, if needed, `uv run pre-commit run --all-files --show-diff-on-failure --color=always` |
| `tests/**` | the edited test file plus the package module it covers |

When in doubt, combine the focused unit files with non-mutating lint:

```bash
uv run ruff format --check bayes_opt tests
uv run ruff check bayes_opt tests
```

## Pytest groups

- Fast unit/component tests: any specific `tests/test_*.py` other than
  `tests/test_notebooks_run.py`.
- Broad unit suite: `uv run pytest tests --ignore=tests/test_notebooks_run.py`.
- Notebook execution suite: `uv run pytest tests/test_notebooks_run.py`. This
  parametrizes over example notebooks, uses `nbconvert`/`nbclient`, and sets a
  600-second cell timeout. It requires the broader development environment and
  can be slow.
- CI-like coverage run: `uv run --no-sync pytest --cov-report xml --cov=bayes_opt/`
  after `uv sync --extra dev`.

## Lint and formatting

Ruff is configured for Python 3.9 target syntax, 110-character line length,
NumPy pydocstyle, import sorting with `bayes_opt` as local, and many bugbear,
pytest, logging, pathlib, NumPy, performance, refurb, and Ruff-specific lint
rules. Docs and examples are excluded in `ruff.toml`; the shell scripts also
focus on `bayes_opt tests`.

Non-mutating checks from `scripts/check.sh`:

```bash
uv run ruff format --check bayes_opt tests
uv run ruff check bayes_opt tests
```

Reference-only scripts:

- `scripts/check.sh` is safe as a non-mutating lint/format check.
- `scripts/check_precommit.sh` installs pre-commit hooks, then runs all files.
  This mutates checkout hooks and is not a routine verification helper.
- `scripts/format.sh` runs Ruff format and Ruff `--fix`; it mutates source
  files and should only be used when intentionally editing.

If the user asks to fix formatting, prefer showing the mutating command before
running it:

```bash
uv run ruff format bayes_opt tests
uv run ruff check bayes_opt --fix
```

## Docs and notebook checks

Docs are Sphinx-based under `docsrc`. The docs workflow uses Python 3.10,
installs `pandoc`, installs development dependencies with `uv sync --extra dev`,
then runs:

```bash
cd docsrc
uv run make github
```

For local iteration, `cd docsrc && uv run make html` is usually enough. The
`github` target builds HTML, copies `docs/html` into `docs`, and copies
`docsrc` into `docs`, so it is more release-like and may update generated docs
output.

`docsrc/conf.py` copies example notebooks into the docs source at import time,
uses autodoc/nbsphinx/IPython highlighting/mathjax/napoleon/intersphinx, and
uses the `sphinx_immaterial` theme. Notebook-related failures can therefore
surface during either `tests/test_notebooks_run.py` or Sphinx docs builds.

## Release and publishing context

Release publishing is intentionally limited:

- The package publish workflow only runs on a published GitHub release.
- It builds the distribution artifacts in CI before upload.
- The upload step is guarded by a PyPI token repository secret.

Do not provide or request PyPI credentials. For maintenance, it is acceptable to
validate build metadata locally with `uv build` when packaging files changed,
but package upload is release-only and secret-protected.

Docs deployment is also workflow-controlled. It publishes docs on releases or
`master` and writes version metadata on the `gh-pages` branch. Local agents
should build docs for validation, not attempt deployment.

## Safe verification sequence

A conservative maintainer sequence is:

1. Install the right environment for the touched surface:
   - small code edits: `uv sync` or an already prepared environment;
   - tests/lint/notebooks/docs: `uv sync --extra dev`.
2. Run focused unit tests from the mapping above.
3. Run non-mutating Ruff checks:
   ```bash
   uv run ruff format --check bayes_opt tests
   uv run ruff check bayes_opt tests
   ```
4. If examples or notebooks changed, run the notebook test explicitly and allow
   extra time.
5. If docs changed, build docs locally with `cd docsrc && uv run make html`; use
   `make github` only when validating release-like generated output.
6. If dependency markers changed, test representative lanes across supported
   Python/NumPy combinations rather than relying on the current interpreter.

The bundled helper can print a plan without running anything:

```bash
python skills/disco/bayesian-optimization/sub-skills/repo-maintenance/scripts/select_native_checks.py bayes_opt/acquisition.py tests/test_acquisition.py
```
