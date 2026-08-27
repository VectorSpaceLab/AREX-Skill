# einops maintainer docs and tests

This reference supports repository maintenance tasks: focused test commands,
backend selection, documentation generation, notebook checks, CI interpretation,
and release/deploy boundaries. It is based on source-evidence names only and is
intended to be used without reading an original checkout.

## Development baseline

| Surface | Repository fact |
|---|---|
| Supported Python | `pyproject.toml` declares `requires-python = ">=3.10"`; ruff target is `py310`. |
| Build backend | Hatchling via `build-system`; Hatch envs define docs, default check, and PyPI scripts. |
| Runtime dependencies | Project metadata declares no runtime/install-time dependencies. |
| Default dev dependencies | `numpy`, `torch`, `jax`, `mlx`, `ruff`, `mypy`, `pytest`, plus notebook helpers `nbformat`, `nbconvert`, `ipython`, `pillow`. |
| Version source | Hatch reads version from `einops/__init__.py`. |
| Distributed tests | README states that tests are distributed as part of the package from einops 0.8.1 onward. |

## Focused package tests

Native command shape:

```bash
python -m einops.tests.run_tests <frameworks> [--pip-install]
```

Examples:

```bash
# Minimal installed-dependency check; no optional framework installation.
python -m einops.tests.run_tests numpy

# Native runner with dependency installation into the current environment.
python -m einops.tests.run_tests numpy pytorch jax --pip-install
```

Safer bundled wrapper:

```bash
# Dry-run only: show env var and command that would run.
python scripts/run_selected_einops_tests.py numpy

# Focus one pytest node while still setting backend semantics correctly.
python scripts/run_selected_einops_tests.py numpy --pytest-target test_ops.py::test_repeat_numpy

# Execute after reviewing the plan.
python scripts/run_selected_einops_tests.py numpy --pytest-target test_ops.py::test_repeat_numpy --execute
```

Focused pytest target paths should be relative to the installed package test
directory, for example `test_ops.py::test_repeat_numpy` or
`test_packing.py::test_pack_unpack_with_numpy`. The wrapper resolves the installed
`einops.tests` package and runs pytest in that directory when `--execute` is set.

`--pip-install` is intentionally not default in either the native runner or the
wrapper. It mutates the active Python environment with `pip install`; use only in
an isolated environment or when the maintainer explicitly wants the runner to
install dependencies.

## Backend selection semantics

### Native runner names

The native `run_tests.py` accepts these framework keys when available for the
current platform:

| Key | Install instruction when `--pip-install` is used | Notes |
|---|---|---|
| `numpy` | `numpy` | Required by README guidance because every framework is tested against numpy. |
| `torch` | `torch --index-url https://download.pytorch.org/whl/cpu` | Native synonym: `pytorch` -> `torch`. |
| `jax` | `jax[cpu]`, `flax` | CPU package instruction. |
| `tensorflow` | `tensorflow` | Native synonym: `tf` -> `tensorflow`. |
| `cupy` | `cupy` | Not in CI matrix because it requires GPU/compatible CUDA. |
| `paddle` | `paddlepaddle` | Native synonym: `paddlepaddle` -> `paddle`. CI comments say Paddle testing is currently dropped. |
| `oneflow` | `oneflow==0.9.0` | CI comments say OneFlow testing is currently dropped. |
| `pytensor` | `pytensor` | Tested separately in CI on Python 3.10 and 3.13. |
| `mlx.core` | `mlx` on macOS, `mlx[cpu]` on Linux | CI includes `mlx.core` in the main backend bundle. |

The package test utilities validate backend names against live backend classes.
Verified live backend names in this source state include `mlx.core`, `pytensor`,
`tinygrad`, `paddle`, `oneflow`, `tensorflow.keras`, `tensorflow`, `cupy`,
`torch`, `numpy`, and `jax`; the native runner exposes only its own install map.

### `EINOPS_TEST_BACKENDS`

`einops/tests/__init__.py` defines `ENVVAR_NAME = "EINOPS_TEST_BACKENDS"`.
`unparse_backends(["numpy", "torch"])` yields:

```text
EINOPS_TEST_BACKENDS=numpy,torch
```

Tests that call `parse_backends_to_test()` fail if this environment variable is
missing. Use the native runner or the bundled wrapper to set it consistently.
When invoking pytest directly, set it yourself:

```bash
EINOPS_TEST_BACKENDS=numpy python -m pytest <installed einops.tests dir>/test_ops.py::test_repeat_numpy
```

Unknown values produce runtime errors. Use the native synonyms only at the runner
or wrapper layer; after normalization, environment values should be backend class
names such as `torch`, not `pytorch`.

## Format, lint, and type checks

`pyproject.toml` defines a default Hatch `check` script:

```toml
check = [
  "ruff format {args:.}",
  "ruff check --fix {args:.}",
  "mypy {args:.}",
]
```

That script is useful when a maintainer wants auto-formatting and auto-fixes.
For non-mutating CI-style checks, use:

```bash
ruff check .
ruff format . --check
mypy .
```

CI pins ruff in the workflow before check-only validation:

```bash
pip install ruff==0.15.8 && ruff check . && ruff format . --check
```

Mypy settings enable `check_untyped_defs`, allow some missing optional framework
imports, and exclude `./docs/utils/` because duplicate `utils` modules confuse
mypy.

## Docs build and README conversion

Hatch docs environment dependencies:

- `mkdocs~=1.6.1`
- `mkdocs-material~=9.5.34`
- `mkdocstrings[python]~=0.26.1`
- `mkdocs-jupyter~=0.25.0`
- `pygments~=2.18.0`

Docs scripts from `pyproject.toml`:

| Hatch script | Command semantics | Mutates generated docs? |
|---|---|---|
| `hatch run docs:convert` | Runs README conversion into docs index. | Yes, writes docs index. |
| `hatch run docs:build` | Convert, then `mkdocs build --clean --strict`. | Yes before build. |
| `hatch run docs:serve` | Convert, then serve on `localhost:8000`. | Yes before serve. |
| `hatch run docs:deploy` | Convert, strict build, then `mkdocs gh-deploy`. | Yes; deploys. |
| `hatch run docs:deploy_force` | Convert, strict build, then `mkdocs gh-deploy --force`. | Yes; credentialed deploy. |

The native README converter removes bare `.mp4` URL lines and writes the result
to `docs_src/index.md`. Use the bundled converter for dry-run-first behavior:

```bash
python scripts/convert_readme_for_docs.py --readme README.md --output docs_src/index.md
python scripts/convert_readme_for_docs.py --readme README.md --output docs_src/index.md --execute
```

`mkdocs.yml` uses `docs_src` as `docs_dir`; tutorial notebooks and
`pytorch-examples.html` are part of navigation. The PyTorch examples HTML is
produced by a separate converter under `scripts/pytorch_examples_source/` and is
best treated as reference-only unless a docs refresh explicitly includes that
pipeline and its extra markdown/pygments dependencies.

## Notebook checks

Native notebook test script assumptions:

- It assumes `torch`, `tensorflow`, and `numpy` are already installed.
- It also needs `nbformat`, `nbconvert`, `jupyter`, and `pillow`.
- It executes notebooks with `ExecutePreprocessor(timeout=120, kernel_name="python3")`.
- Notebook 2 is tested with replacements for both `pytorch` and `tensorflow`.

CI notebook workflow installs:

```bash
uv pip install nbformat nbconvert jupyter pillow pytest numpy tensorflow
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -e . && uv run pytest scripts/test_notebooks.py
```

Bundled safe checker:

```bash
# List notebooks and dependency availability without executing notebooks.
python scripts/notebook_execution_check.py --list

# Dry-run a selected notebook execution plan.
python scripts/notebook_execution_check.py --notebook docs/1-einops-basics.ipynb

# Execute a selected notebook with bounded timeout.
python scripts/notebook_execution_check.py --notebook docs/1-einops-basics.ipynb --execute --timeout 120
```

Notebook execution can be slow and may import heavy frameworks. Prefer listing
and dependency checks before execution, and avoid running all notebooks unless
optional dependencies and time budget have been approved.

## CI matrix notes

### Main tests

The main test workflow runs on push and pull request with `fail-fast: false`.
The matrix uses Python `3.10`, `3.11`, and `3.13` for:

```text
numpy pytorch tensorflow jax mlx.core
```

Additional matrix entries run `pytensor` on Python `3.10` and `3.13`.
Workflow comments state:

- TensorFlow, OneFlow, and Paddle have had protobuf-version conflicts.
- CuPy is not tested because it demands GPU.
- OneFlow testing is dropped due to upstream issues.
- Paddle testing is dropped due to divergence with NumPy in Python 3.10 and
  `paddle==2.6.1`.

Each job checks ruff compliance, then installs the package editable and runs:

```bash
python -m einops.tests.run_tests ${{ matrix.frameworks }} --pip-install
```

### Notebook tests

The notebook workflow runs on Python `3.10` and `3.13`, uses `uv`, installs
notebook dependencies plus CPU PyTorch, then runs pytest over the native notebook
script.

### Docs deploy

Docs deploy triggers on pushes to `main` and `docs-deploy-testing`. It grants
`contents: write`, configures GitHub bot credentials, installs Hatch, and runs:

```bash
hatch run docs:deploy_force
```

This is a repository-write deployment path and should not be treated as a local
safe default.

### PyPI deploy

PyPI deploy triggers on GitHub release creation, installs `uv`, sets
`UV_PUBLISH_TOKEN` from the `PYPI_TOKEN` secret, then runs:

```bash
uv build
uv publish
```

## Release and deploy boundaries

Allowed safe maintainer guidance in this sub-skill:

- Identify release scripts and their boundaries.
- Distinguish build-only inspection from publish/deploy operations.
- Warn when a command requires GitHub repository write permissions or PyPI
  credentials.
- Explain that `--pip-install`, docs conversion, and Hatch `check` can mutate
  local state.

Do not provide step-by-step credential setup, secret creation, or human release
approval flows. Do not run `mkdocs gh-deploy`, `hatch run docs:deploy*`,
`uv publish`, or `hatch run pypi:deploy*` unless a human maintainer explicitly
authorizes the credentialed action and owns the target credentials.
