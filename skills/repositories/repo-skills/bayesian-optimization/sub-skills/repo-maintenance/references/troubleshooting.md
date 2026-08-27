# BayesianOptimization maintenance troubleshooting

Use this reference when a checkout-maintenance command fails. It assumes the
agent is editing a source checkout and should keep package-runtime advice in the
other sub-skills.

## Dependency marker and Python/NumPy conflicts

Symptoms:

- Resolver errors involving NumPy, SciPy, scikit-learn, or `packaging`.
- NumPy 1 selected on Python 3.13 or newer.
- SciPy or scikit-learn versions too old for Python 3.14.
- CI passes one Python/NumPy lane but fails another.

Checks:

```bash
python --version
uv run python - <<'PY'
import numpy, scipy, sklearn, packaging
print('numpy', numpy.__version__)
print('scipy', scipy.__version__)
print('sklearn', sklearn.__version__)
print('packaging', packaging.__version__)
PY
```

Resolution path:

1. Compare the interpreter to the `pyproject.toml` markers:
   - runtime supports Python `>=3.9`;
   - NumPy 1 is only supported below Python 3.13;
   - Python 3.14 requires newer NumPy, SciPy, scikit-learn, and `packaging`.
2. If reproducing CI, use `uv sync --extra dev`, then pin the NumPy lane:
   ```bash
   uv pip install "numpy>=1.25,<2" "scipy<1.18"
   uv pip install "numpy>=2"
   ```
   Run only one lane in an environment at a time.
3. If editing dependency markers, test representative lanes rather than only the
   current local Python. At minimum cover an older Python with NumPy 1, the same
   or newer Python with NumPy 2, and a Python 3.13+ lane where NumPy 1 is
   intentionally unavailable.
4. Treat free-threaded Python 3.14 (`3.14t`) as a CI compatibility lane; avoid
   claiming local coverage unless that interpreter was actually used.

## Ruff failures

Symptoms:

- `uv run ruff format --check bayes_opt tests` reports files that would be
  reformatted.
- `uv run ruff check bayes_opt tests` reports lint violations.
- Rules differ between docs/examples and package/tests.

Resolution path:

1. Remember the configured scope: `ruff.toml` excludes `docsrc/**/*` and
   `examples/**/*`; scripts check `bayes_opt tests`.
2. For non-mutating verification, run:
   ```bash
   uv run ruff format --check bayes_opt tests
   uv run ruff check bayes_opt tests
   ```
3. If the user wants fixes, warn that the next commands mutate files:
   ```bash
   uv run ruff format bayes_opt tests
   uv run ruff check bayes_opt --fix
   ```
4. If tests fail on Bandit `assert` warnings, note the configured per-file
   ignore: `tests/test_*.py` ignores `S101` and pydocstyle `D`. A warning there
   may indicate the file did not match the expected test filename pattern.
5. If import-order failures appear, use the local-folder rule for `bayes_opt` and
   keep `from __future__ import annotations` required at the top of Python files
   that Ruff manages.

## Pre-commit failures or hook confusion

Symptoms:

- `scripts/check_precommit.sh` changes `.git/hooks`.
- `pre-commit` reports failures not seen in direct Ruff commands.
- Hook installation is unexpected during routine validation.

Resolution path:

1. Do not use `scripts/check_precommit.sh` as a routine read-only check; it runs
   `uv run pre-commit install` before checking all files.
2. For CI-like pre-commit verification without installing hooks, use:
   ```bash
   uv run pre-commit run --all-files --show-diff-on-failure --color=always
   ```
3. If a hook fails, inspect `.pre-commit-config.yaml`: it uses Ruff lint and
   Ruff format hooks from `ruff-pre-commit`. Align fixes with the Ruff commands
   above.
4. If hook state is the problem, explain that hook installation is a checkout
   side effect and should not be part of ordinary agent verification unless the
   maintainer requested hook setup.

## Notebook execution timeouts

Symptoms:

- `tests/test_notebooks_run.py` fails with a cell execution error.
- Notebook execution exceeds the 600-second cell timeout.
- Missing kernel, `nbclient`, `nbconvert`, `nbformat`, matplotlib, or notebook
  dependencies.

Resolution path:

1. Use the development environment: `uv sync --extra dev`.
2. Run the notebook suite only when examples/notebooks, notebook dependencies,
   or docs notebook rendering changed:
   ```bash
   uv run pytest tests/test_notebooks_run.py
   ```
3. To isolate a failure, run the same test with `-k` matching the notebook name
   or execute the notebook manually in a throwaway copy. Keep generated notebook
   outputs out of the runtime skill tree.
4. If the failure is stochastic or slow optimization, first reduce notebook work
   in the example itself only if the change is intentionally updating examples;
   otherwise report that full notebook validation is slow and rerun once before
   treating it as a code regression.
5. If the test cannot find notebooks, check that it expects notebooks under the
   repository `examples` directory.

## Docs, pandoc, and Sphinx failures

Symptoms:

- `cd docsrc && uv run make html` or `make github` fails.
- `nbsphinx` or notebook conversion errors appear during docs build.
- Pandoc is missing.
- Theme or autodoc import errors occur.

Resolution path:

1. Use `uv sync --extra dev`; docs dependencies are part of the broad dev extra.
   `docsrc/requirements.txt` lists a smaller docs set (`sphinx`, `nbsphinx`,
   `sphinx_rtd_theme`), but CI uses the dev extra and the configured theme is
   `sphinx_immaterial`.
2. Install `pandoc` when reproducing the docs workflow locally. The GitHub
   workflow installs it with the system package manager before building.
3. Prefer local iteration with:
   ```bash
   cd docsrc
   uv run make html
   ```
   Use `uv run make github` when validating the workflow-like target that copies
   generated output.
4. Remember that `docsrc/conf.py` adds the repository parent to `sys.path` and
   copies example notebooks into the docs source. Import failures may be caused
   by running from the wrong directory or by an uninstalled/incorrect checkout.
5. If docs build creates or updates generated docs artifacts, keep those changes
   separate from runtime skill files and only commit them when release/docs
   policy requires it.

## Editable install and import confusion

Symptoms:

- Tests import an installed `bayesian-optimization` package from elsewhere
  instead of the edited checkout.
- `import bayes_opt` works in one shell but not under `uv run`.
- Sphinx autodoc imports stale code.

Checks:

```bash
uv run python - <<'PY'
import bayes_opt
print(bayes_opt.__file__)
PY
```

Resolution path:

1. Run commands from the checkout root unless a command explicitly says
   `cd docsrc`.
2. Use `uv sync` or `uv sync --extra dev` so `uv run` resolves the checkout and
   its declared dependencies consistently.
3. Avoid mixing an external virtual environment with `uv run` from the checkout.
4. For docs, `docsrc/conf.py` inserts the checkout parent into `sys.path`; if
   autodoc imports unexpected code, verify the working directory and
   `bayes_opt.__file__` under `uv run`.
5. Remove stale generated files or notebook copies only when they are generated
   checkout artifacts, not runtime skill assets.

## Pytest failures after focused changes

Symptoms:

- Focused tests pass, but the full suite fails in related modules.
- Categorical/integer parameter changes break acquisition or target-space tests.
- Constraint behavior fails only in integration tests.

Resolution path:

1. Expand from the touched-file mapping in `development-workflows.md`:
   - acquisition changes often need optimizer and constraint integration tests;
   - parameter changes often need target-space and optimizer tests;
   - target-space changes often need optimizer tests;
   - constraint changes often need acquisition constrained integration tests.
2. Use explicit test files before a full suite to keep feedback focused.
3. Escalate to `uv run pytest tests --ignore=tests/test_notebooks_run.py` when a
   change touches public API, shared random-state handling, bounds conversion,
   serialization, or dependency compatibility.
4. Run notebook tests separately because they are slow and have different
   failure modes.

## Publish credential limits

Symptoms:

- User asks to publish to PyPI or asks for release credentials.
- A package upload attempt fails because release secrets are unavailable.
- A package-build check is confused with release publishing.

Boundary:

- Do not provide credentialed publish instructions, request secrets, or attempt
  to bypass repository release workflows.
- Publishing is guarded by a PyPI token repository secret and only runs on
  published releases.
- Maintainer agents may suggest or run `uv build` for local packaging validation
  when packaging files changed, but should stop before upload.

Safe response:

```text
Local build validation can use `uv build`. PyPI upload is release-only and
secret-protected in the repository workflow; I will not handle credentials or
publish from this maintenance session.
```
