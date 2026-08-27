# LightFM Build and Maintenance Troubleshooting

Use this reference for repository-maintenance failures. For user-facing modeling, data, or metric behavior, route through the sibling sub-skills named in `SKILL.md` instead of diagnosing from build-system symptoms.

## Quick triage sequence

1. Confirm the active Python environment is the one that installed the checkout:

   ```bash
   python -m pip show lightfm
   python -c "import lightfm; print(lightfm.__version__)"
   ```

2. Reinstall editable after source or generated C changes:

   ```bash
   python -m pip install -e .
   ```

3. Run the bundled diagnostic from this sub-skill directory:

   ```bash
   python scripts/check_lightfm_install.py --tiny-run
   ```

4. Run the smallest relevant pytest target from the checkout root before broader tests.

## Missing compiled extension import

Symptoms:

- `ModuleNotFoundError` or `ImportError` mentioning `lightfm._lightfm_fast`.
- `ImportError` for both `lightfm._lightfm_fast_openmp` and `lightfm._lightfm_fast_no_openmp`.
- `LightFM` import fails before reaching user code.

Likely causes and fixes:

| Cause | Fix |
|---|---|
| Editable install was not rebuilt after checkout changes | Run `python -m pip install -e .`, then rerun the diagnostic. |
| Build artifacts were compiled for a different Python ABI | Reinstall from the same Python that will run tests; remove stale local build artifacts only if you are sure they are generated. |
| Compiler or Python development headers are missing | Install the platform compiler toolchain and Python headers for the active Python, then reinstall editable. |
| OpenMP extension failed and no fallback extension was built | Inspect compiler output; try a no-OpenMP platform/build or fix OpenMP runtime/toolchain. |
| Import path is shadowing the intended checkout/package | Run the diagnostic to print the imported module origins and compare them with the active environment. |

Acceptable fallback: on macOS/Windows, or an intentional no-OpenMP build, `lightfm._lightfm_fast` may warn that OpenMP support is unavailable and still import the no-OpenMP extension. That is a CPU single-thread fallback, not a functional failure.

## OpenMP compiler or runtime failures

Linux builds try the OpenMP extension by default using `-fopenmp` at compile and link time. Failures commonly mention missing `omp.h`, unsupported `-fopenmp`, missing `libgomp`, or unresolved OpenMP symbols.

Remediation options:

- Use a compiler/runtime pair that supports OpenMP, commonly GCC plus the matching OpenMP runtime on Linux.
- Ensure both compile and link steps receive OpenMP support; fixing compile only can still leave runtime import failures.
- If the failure is an optimization flag rather than OpenMP itself, set:

  ```bash
  LIGHTFM_NO_CFLAGS=1 python -m pip install -e .
  ```

- If the user only needs correctness and the platform intentionally lacks OpenMP, use or test the no-OpenMP extension. Do not claim multithreaded speedups in that environment.

Platform expectations:

| Platform | Expected behavior |
|---|---|
| Linux | OpenMP extension is selected by setup by default when available. Missing OpenMP should be treated as a build/runtime issue unless an intentional fallback is documented. |
| macOS | No-OpenMP extension is selected by setup by default. OpenMP warnings are expected if the wrapper falls back. |
| Windows | No-OpenMP extension is selected by setup by default. Use the compiler toolchain compatible with the active Python. |

## `-march=native` or optimization flag failures

By default, setup adds `-ffast-math`, and on non-macOS platforms also adds `-march=native`. Some constrained compilers, cross-compilation targets, containers, or unusual CPUs may reject these flags.

Use:

```bash
LIGHTFM_NO_CFLAGS=1 python -m pip install -e .
```

This omits LightFM's custom optimization flags. It does not disable OpenMP selection on Linux.

## Cython is missing

Symptoms:

- `python setup.py cythonize` fails with `ModuleNotFoundError: No module named 'Cython'`.
- Template edits do not appear in generated C files.

Fix:

```bash
python -m pip install Cython
python setup.py cythonize
python -m pip install -e .
```

Cython is needed only when regenerating from the template. Normal editable/source builds consume generated C files and should not require Cython unless the build path has been changed.

## Generated C files are stale

Symptoms:

- Template or algorithm changes pass Python review but compiled behavior is unchanged.
- Diffs include the template but not `lightfm/_lightfm_fast_openmp.c` or `lightfm/_lightfm_fast_no_openmp.c`.
- Linux and no-OpenMP behavior diverge unexpectedly after a shared template change.

Fix and verification:

```bash
python -m pip install Cython
python setup.py cythonize
python -m pip install -e .
python -m pytest tests/test_fast_functions.py tests/test_api.py
```

After regeneration, verify both generated C variants reflect the intended change. The generated `.pyx` variant files are local byproducts and should not be treated as the durable source of truth.

## Pip build isolation and source builds

If a packaging front-end builds in isolation, the build environment may not contain the compiler, headers, runtime libraries, or Cython needed for the selected path. Symptoms can look different from an editable build because the isolated environment is separate from the runtime environment.

Options:

- Prefer editable install in a prepared local environment for maintainer diagnosis:

  ```bash
  python -m pip install -e .
  ```

- If an isolated build is failing only because it cannot see already-prepared build tools, retry in a disposable environment with:

  ```bash
  python -m pip install --no-build-isolation -e .
  ```

- Do not use `--no-build-isolation` to hide undeclared release-build requirements. For packaging changes, make the dependency expectation explicit and retest clean builds.

## Tests fail only under multithreading

Symptoms:

- `num_threads=1` passes but `num_threads>1` fails or gives unstable results.
- Linux OpenMP tests differ from macOS/Windows no-OpenMP behavior.

Triage:

```bash
python -m pytest tests/test_fast_functions.py
python -m pytest tests/test_api.py -k "rank or multithread or predict"
python -m pytest tests/test_movielens.py -k "multithreaded"
```

Interpretation:

- OpenMP races belong in the generated OpenMP C path or shared template sections that use parallel loops and locks.
- If no-OpenMP platforms pass, still treat Linux OpenMP instability as a real bug for CPU-threaded training.
- If the no-OpenMP backend is active, `num_threads` cannot provide OpenMP speedup.

## Dataset-oriented tests fail or hang

Some tests exercise public dataset fetchers. Failures may be caused by cache state, network access, dataset availability, or slow downloads rather than package logic.

Use in-memory tests first when diagnosing build or model-core changes:

```bash
python -m pytest tests/test_fast_functions.py tests/test_api.py tests/test_data.py tests/test_evaluation.py
```

Then run dataset-oriented tests only when the change touches fetchers, cross-validation on fetched data, or release-level behavior:

```bash
python -m pytest tests/test_cross_validation.py tests/test_datasets.py tests/test_movielens.py
```

## Lint command mismatch

The repository configuration and CI use slightly different flake8 purposes:

- Configuration sets style defaults such as line length and ignored rules.
- CI first fails on syntax/undefined-name categories.
- CI then runs a broader warning summary with `--exit-zero` and a 127-character line length.

When reproducing CI, run both CI commands from the maintenance reference rather than only a local editor or pre-commit check.

## Docs generation hazards

Safe local docs build:

```bash
python -m pip install -r docs-requirements.txt
cd doc
make html
```

Mutation-heavy docs example generation:

```bash
make examples
```

Use `make examples` only when intentionally refreshing generated RST/assets from notebooks. Review the resulting doc/example asset changes before committing.

Publication hazard:

```bash
make update-docs
```

Do not run `update-docs` unless the user explicitly authorizes release publication. It fetches `gh-pages`, checks it out, removes and recreates published `docs/`, commits, and pushes. It can disrupt local branch state and publish unintended docs.

## When to narrow scope

If the user's request is simply to train a recommender, evaluate ranking metrics, or construct feature matrices, stop repo-maintenance debugging and route to the appropriate sibling sub-skill. Build-system work is justified only when the failure is in installation, imports, compiled routines, test/lint/docs infrastructure, or CI behavior.
