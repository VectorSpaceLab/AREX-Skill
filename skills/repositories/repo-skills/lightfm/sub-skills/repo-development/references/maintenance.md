# LightFM Maintenance Reference

This reference is for maintainers working inside a LightFM source checkout. Keep commands scoped to the active checkout and to the active Python environment. Prefer a disposable virtual environment when testing build-system or compiler changes.

## Package and editable install

LightFM is distributed as the `lightfm` Python package, version `1.17` for the source version covered by this skill. It is CPU-only.

| Goal | Command | Notes |
|---|---|---|
| Install released package with pip | `python -m pip install lightfm` | End-user baseline; not sufficient for testing local source edits. |
| Install released package with conda | `conda install -c conda-forge lightfm` | End-user baseline from conda-forge. |
| Create a local virtual environment | `python3 -m venv .venv` then activate it | Use any equivalent isolated environment manager if preferred. |
| Upgrade installer | `python -m pip install --upgrade pip` | Matches CI's explicit pip upgrade step. |
| Install local checkout editable | `python -m pip install -e .` | Builds the compiled extension variant selected by platform/build configuration. |
| Install test requirements | `python -m pip install -r test-requirements.txt` | Test requirements declare `pytest`; editable install supplies runtime dependencies. |
| Install lint requirements | `python -m pip install -r lint-requirements.txt` | Includes pinned `pre-commit`, `black`, and `flake8`. |
| Install docs requirements | `python -m pip install -r docs-requirements.txt` | Includes Sphinx and the Read the Docs theme; notebook-to-RST generation may need Jupyter tooling too. |

## Compiled extension variants

LightFM imports compiled routines through `lightfm._lightfm_fast`, which first tries the OpenMP extension and then falls back to the no-OpenMP extension with a warning.

| Variant | Module | Generated C source | Expected build selection |
|---|---|---|---|
| OpenMP | `lightfm._lightfm_fast_openmp` | `lightfm/_lightfm_fast_openmp.c` | Linux by default, using `-fopenmp` for compile and link. |
| No OpenMP | `lightfm._lightfm_fast_no_openmp` | `lightfm/_lightfm_fast_no_openmp.c` | macOS and Windows by default; also the runtime fallback when OpenMP import fails. |
| Wrapper | `lightfm._lightfm_fast` | Python wrapper | The public internal import used by `LightFM`. |

Important build facts:

- The package has no GPU path. OpenMP only controls CPU multithreading.
- Linux builds use the OpenMP extension by default. macOS and Windows intentionally build the no-OpenMP extension by default.
- Unless `LIGHTFM_NO_CFLAGS=1` is set, setup adds `-ffast-math`; on non-macOS platforms it also adds `-march=native`.
- `LIGHTFM_NO_CFLAGS=1` disables those optimization flags, but it does not by itself select no-OpenMP on Linux.
- If OpenMP is unavailable at runtime, the wrapper warning means only one CPU thread will be used.

## Cython template and generated C files

Use this flow when editing the Cython template or any generated extension source:

```bash
python -m pip install Cython
python setup.py cythonize
python -m pip install -e .
python -m pytest tests/test_fast_functions.py tests/test_api.py
```

What the Cython command does:

1. Renders `lightfm/_lightfm_fast_no_openmp.pyx` and `lightfm/_lightfm_fast_openmp.pyx` from the shared template.
2. Cythonizes those generated `.pyx` files into the corresponding `.c` files.
3. Leaves the `.pyx` variant files as generated local byproducts; they are ignored by the repository configuration.
4. Updates the generated `.c` files that are packaged and used for source builds.

Recommended checks after Cython work from the checkout root:

```bash
python -m pip install -e .
python -m pytest tests/test_fast_functions.py
python -m pytest tests/test_api.py
```

Also run the bundled install diagnostic from this sub-skill directory, using the same Python environment:

```bash
python scripts/check_lightfm_install.py --tiny-run
```

When reviewing the result, ensure intended algorithm/template changes appear in both generated C variants. If only the template changed and C files did not, downstream source builds may use stale compiled code.

## Focused tests

Use focused tests before full-suite runs:

| Maintenance change | Focused command | Why |
|---|---|---|
| Extension import, CSR wrapper, low-level helper | `python -m pytest tests/test_fast_functions.py` | Verifies compiled helper symbols and CSR access. |
| Model API, fit/predict, sparse matrix dtypes, rank prediction | `python -m pytest tests/test_api.py` | Exercises core `LightFM` behavior and extension calls. |
| Dataset mapping and feature construction | `python -m pytest tests/test_data.py` | In-memory checks for `Dataset` and feature matrices. |
| Evaluation metrics or rank intersection behavior | `python -m pytest tests/test_evaluation.py` | In-memory metric checks against alternative implementations. |
| Split behavior | `python -m pytest tests/test_cross_validation.py` | In-memory random split/disjointness checks; no dataset download required. |
| Dataset fetchers | `python -m pytest tests/test_datasets.py` | May download/cache public datasets; StackExchange case is skipped in-source for memory. |
| MovieLens accuracy/regression behavior | `python -m pytest tests/test_movielens.py` | Slower and data-dependent; useful before release or algorithm changes. |
| Broad safety pass | `python -m pytest` | Matches CI's test entry point. |

Prefer `python -m pytest ...` so the active environment's Python and installed editable package are used consistently.

## Lint and formatting

Install lint requirements only when linting or preparing PR-quality changes:

```bash
python -m pip install -r lint-requirements.txt
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

Local formatting/lint hooks are optional:

```bash
python -m pip install pre-commit
pre-commit install
```

The repository configuration sets flake8 `max-line-length = 100`, ignores `I100`, `W503`, and `E203`, and excludes generated/build/docs-oriented directories. CI additionally runs a 127-character warning summary command.

## Docs and example generation

Local docs build after docs/source changes:

```bash
python -m pip install -r docs-requirements.txt
cd doc
make html
```

Notebook-to-RST example generation is a maintainer mutation workflow:

```bash
make examples
```

Use `make examples` only when intentionally refreshing generated documentation from notebooks. It converts notebooks to RST, moves generated RST under `doc/`, and copies generated notebook asset directories.

Do not run this by default:

```bash
make update-docs
```

`update-docs` installs the package, builds docs, fetches and checks out `gh-pages`, deletes and recreates published `docs/`, commits, and pushes. Treat it as a release/publication operation requiring explicit branch and push approval.

## CI expectations

The observed GitHub Actions workflow runs on pushes and pull requests to `master` with this matrix:

| OS | Python versions | Extension expectation |
|---|---|---|
| Ubuntu latest | 3.7, 3.11 | OpenMP build by default if compiler/runtime support exists. |
| macOS latest | 3.11 | No-OpenMP build by default. |
| Windows latest | 3.11 | No-OpenMP build by default. |

CI steps:

1. Check out source.
2. Set up the selected Python.
3. Upgrade pip and install `flake8 pytest`.
4. Run strict flake8 syntax/undefined-name checks.
5. Run broad flake8 warning summary.
6. Install editable with `pip install -e .`.
7. Run `pytest`.

When a change touches build logic, test on at least one Linux environment for OpenMP and one no-OpenMP environment or configured no-OpenMP build before treating platform coverage as complete.
