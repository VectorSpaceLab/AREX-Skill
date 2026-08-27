# einops maintainer troubleshooting

Use this when repository development commands fail or when a maintainer needs to
understand which operations are safe, mutating, optional, or credentialed.

## Missing `EINOPS_TEST_BACKENDS`

Symptom examples:

```text
RuntimeError: Testing frameworks were not specified, env var EINOPS_TEST_BACKENDS not set
```

Cause: package tests called `parse_backends_to_test()` without the runner setting
backend selection.

Fixes:

1. Prefer the native runner:
   ```bash
   python -m einops.tests.run_tests numpy
   ```
2. Or use the bundled dry-run-first wrapper:
   ```bash
   python scripts/run_selected_einops_tests.py numpy --pytest-target test_ops.py::test_repeat_numpy --execute
   ```
3. If invoking pytest directly, set the environment variable using normalized
   backend names:
   ```bash
   EINOPS_TEST_BACKENDS=numpy python -m pytest <installed-test-dir>/test_ops.py::test_repeat_numpy
   ```

Do not set synonyms such as `pytorch` inside `EINOPS_TEST_BACKENDS`; normalize to
`torch` first.

## Unrecognized framework names or synonyms

Symptom examples:

```text
RuntimeError: Unrecognized frameworks: ['pytorch-cpu']
RuntimeError: Unknown framework: pytorch
```

Native runner synonyms are limited:

| User spelling | Normalized backend |
|---|---|
| `pytorch` | `torch` |
| `tf` | `tensorflow` |
| `paddlepaddle` | `paddle` |

Common corrections:

- Use `torch`, or `pytorch` only through the native runner/wrapper.
- Use `tensorflow`, or `tf` only through the native runner/wrapper.
- Use `mlx.core`, not `mlx`, for backend selection in the test runner.
- Do not invent hardware suffixes such as `torch-cuda` or `jax-gpu`; manage
  hardware-specific package installation in the environment and keep backend
  names unchanged.

## Optional framework install conflicts

Symptom examples:

- TensorFlow, OneFlow, or Paddle dependency resolver failures.
- Protobuf version conflicts after broad `--pip-install` use.
- A previously working environment changes after test setup.

Cause: the native runner's `--pip-install` installs optional backend packages
into the current environment. CI comments explicitly warn about conflicts among
TensorFlow, OneFlow, and Paddle protobuf requirements; CI also drops OneFlow and
Paddle testing in the current matrix.

Fixes:

1. Use the smallest backend set that covers the change, usually starting with
   `numpy`.
2. Avoid `--pip-install` in a shared or user-important environment.
3. Use a fresh isolated environment for conflicting optional frameworks.
4. Split backend families into separate environments if resolver conflicts are
   the problem.
5. Treat CuPy as GPU/accelerator-specific; do not expect it to pass in a generic
   CPU-only CI-like environment.

## `--pip-install` mutates the current environment

Symptom examples:

- New or upgraded packages appear after running tests.
- Optional framework packages downgrade shared dependencies.
- The `pip` used is not the one the maintainer intended.

Cause: native `run_tests.py` shells out to `pip install ...` when `--pip-install`
is provided. Its usage text says to make sure `pip` points to the right pip.

Safer pattern:

```bash
# Inspect first.
python scripts/run_selected_einops_tests.py numpy --pip-install

# Execute only in an intentionally disposable/isolated environment.
python scripts/run_selected_einops_tests.py numpy --pip-install --execute
```

When in doubt, omit `--pip-install`, install only the needed packages explicitly,
and rerun without environment mutation.

## Missing pytest or optional backend imports

Symptom examples:

```text
No module named pytest
backend could not be initialized for tests
No module named torch / tensorflow / jax / pytensor
```

Fixes:

- Install `pytest` for any test run.
- Install `numpy`; README says every framework is tested against numpy.
- Add one optional framework at a time and rerun the smallest focused target.
- If a backend initialization warning appears for a backend not relevant to the
  current change, narrow `EINOPS_TEST_BACKENDS` rather than installing every
  framework.

## Notebook dependency failures

Symptom examples:

```text
ModuleNotFoundError: No module named 'nbformat'
ModuleNotFoundError: No module named 'nbconvert'
No module named 'jupyter'
No module named 'PIL'
No module named 'tensorflow'
No module named 'torch'
```

Native notebook tests assume these are available: `nbformat`, `nbconvert`,
`jupyter`, `pillow`, `numpy`, `tensorflow`, and `torch`.

Safe diagnosis:

```bash
python scripts/notebook_execution_check.py --list
```

CI-like installation shape:

```bash
uv pip install nbformat nbconvert jupyter pillow pytest numpy tensorflow
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Do not install heavyweight frameworks into a shared environment without approval.
Use an isolated environment if the notebook check requires TensorFlow and PyTorch
together.

## Notebook timeouts or slow execution

Symptom examples:

```text
CellExecutionError
TimeoutError
A cell timed out while it was being executed
```

Native notebook execution uses a 120-second per-cell timeout and a `python3`
kernel. Slow or hanging cells may be caused by framework import time, first-time
compilation, network attempts, or local resource constraints.

Fixes:

1. Execute a single named notebook first:
   ```bash
   python scripts/notebook_execution_check.py --notebook docs/1-einops-basics.ipynb --execute --timeout 120
   ```
2. Increase timeout only after confirming the notebook is expected to be slow:
   ```bash
   python scripts/notebook_execution_check.py --notebook docs/2-einops-for-deep-learning.ipynb --execute --timeout 240
   ```
3. For notebook 2 backend-sensitive behavior, ensure both PyTorch CPU and
   TensorFlow are installed if attempting CI-equivalent coverage.
4. Avoid running all notebooks when the task only changes README prose or API
   docs.

## README conversion mutates docs

Symptom examples:

- `docs_src/index.md` changes after `hatch run docs:build` or `hatch run docs:serve`.
- Bare README `.mp4` URL lines disappear in generated docs index.

Cause: docs Hatch scripts run the README converter before build/serve/deploy. The
native converter reads `README.md`, removes bare `.mp4` URL lines, and writes
`docs_src/index.md`.

Safe workflow:

```bash
# Preview only; writes nothing.
python scripts/convert_readme_for_docs.py --readme README.md --output docs_src/index.md

# Apply intentionally.
python scripts/convert_readme_for_docs.py --readme README.md --output docs_src/index.md --execute
```

After applying, review the docs index diff before committing. Do not assume docs
build is read-only.

## Docs deploy warnings

Symptom examples:

- `mkdocs gh-deploy` asks for credentials or fails with permission errors.
- A local run attempts to push to `gh-pages` or repository pages infrastructure.

Cause: deploy commands are credentialed write operations. The GitHub workflow
sets bot Git identity, grants `contents: write`, and runs a force deploy script.

Boundaries:

- Safe locally: `hatch run docs:build` or `hatch run docs:serve` after reviewing
  README conversion mutation.
- Not a default local action: `hatch run docs:deploy`,
  `hatch run docs:deploy_force`, or raw `mkdocs gh-deploy`.
- Run deploy only when a human maintainer explicitly owns/approves the target
  repository credentials.

## PyPI token and publish boundaries

Symptom examples:

```text
UV_PUBLISH_TOKEN is not set
403 Forbidden
Invalid or non-user-scoped token
Package already exists
```

Cause: PyPI deployment is performed by GitHub release workflow using
`UV_PUBLISH_TOKEN` from the repository secret `PYPI_TOKEN`.

Boundaries:

- Safe packaging rehearsal can stop at build artifact creation in an isolated
  environment if requested by a maintainer.
- Do not run `uv publish`, `hatch run pypi:deploy`, or
  `hatch run pypi:deploy_test` as a generic troubleshooting step.
- Do not create, request, print, or store PyPI tokens in generated skill files or
  logs.
- If publish fails in CI, investigate workflow configuration and package
  metadata, but leave credential rotation and release approval to the project
  maintainers.

## Ruff/mypy surprises

Symptom examples:

- `hatch run check` edits files.
- Ruff reports formatting differences when CI used check-only commands.
- Mypy complains about docs utility modules or optional framework imports.

Facts:

- Hatch `check` is mutating: `ruff format`, `ruff check --fix`, then `mypy`.
- CI ruff validation is non-mutating: `ruff check .` and `ruff format . --check`.
- Mypy excludes `./docs/utils/` and ignores missing imports for several optional
  framework modules.

Fixes:

- Use CI-style commands for verification-only review.
- Use Hatch `check` when intentionally applying formatting/fixes.
- Keep optional backend typing failures separate from runtime backend smoke
  failures.

## Staleness and refresh checks

Refresh the repo skill before giving confident maintainer instructions when:

- `pyproject.toml` changes Hatch envs, Python support, ruff/mypy settings, or
  release scripts.
- `einops/tests/run_tests.py` changes framework keys, synonyms, install
  instructions, or env var handling.
- `einops/tests/__init__.py` changes `EINOPS_TEST_BACKENDS` parsing.
- `scripts/convert_readme.py` changes docs mutation semantics.
- `scripts/test_notebooks.py` changes dependencies, notebook selection, backend
  replacements, or timeout.
- GitHub workflow matrices or deploy triggers change.
- `mkdocs.yml` changes docs source directory, nav, or plugin requirements.
