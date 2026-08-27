# Repository Maintenance And Focused Tests

Use this reference when maintaining metadata scripts, AutoSklearn2 selector or
portfolio data, ASLib parsing/writing, or the `automl_common` submodule. Keep the
scope narrow: most metadata tests are network-bound or expensive.

## Submodule checks

The `autosklearn.automl_common` package area is a git submodule. A maintenance
working tree should have it initialized before running tests or editing code
that imports from it.

Suggested checks:

```bash
git submodule status --recursive
python -c "import autosklearn.automl_common.common; print('automl_common import ok')"
```

If the submodule line starts with `-`, it has not been initialized. If it starts
with `+`, it is checked out at a different commit than the superproject expects.
Use the repository's standard submodule update workflow before debugging Python
imports.

## Pytest defaults and focused commands

Project pytest configuration sets:

```toml
[tool.pytest.ini_options]
testpaths = ["test"]
minversion = "3.7"
addopts = "--forked"
```

CI runs pytest with additional arguments equivalent to:

```bash
python -m pytest --forked --durations=20 --timeout=600 --timeout-method=thread -s test
```

For metadata maintenance, use progressively wider commands:

```bash
# 1. Always cheap: bundled dry helper parser check
python scripts/metadata_command_template.py --help

# 2. Cheap import boundary checks
python -c "import autosklearn; import autosklearn.experimental.askl2; import autosklearn.experimental.selector"
python -c "import autosklearn.metalearning.mismbo; import autosklearn.metalearning.input.aslib_simple"

# 3. Focused pytest selection; warn first because this can use OpenML and bounded AutoML
python -m pytest -k "metadata_generation or metalearning or selector" --forked --timeout=600 --timeout-method=thread -s

# 4. If a previous pytest failed, iterate only failures before widening
python -m pytest --last-failed --forked --timeout=600 --timeout-method=thread -s
```

Do not run full pytest by default during a short Researcher task. If full pytest
is approved, set BLAS thread limits to avoid oversubscription:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
python -m pytest --forked --durations=20 --timeout=600 --timeout-method=thread -s test
```

## CI matrix facts

The maintained CI matrix targets Python 3.7, 3.8, and 3.9. Source and conda
installs are exercised on Ubuntu, and one source distribution install is checked
on Ubuntu with Python 3.7. Windows and macOS entries appear in the matrix but are
excluded by the workflow because the test commands and dependency setup are
Linux-oriented.

The CI flow also:

- checks out submodules recursively;
- installs test extras for source, conda, or distribution installs;
- caps the test job at 120 minutes;
- applies BLAS thread environment variables before pytest;
- records git status before tests and fails if generated files are left behind
  afterwards, except for cleanup of pytest cache.

These facts matter when reproducing CI failures locally: local success without
submodules, timeouts, thread caps, or dirty-tree checks may not match CI.

## Contributor workflow for metadata script edits

1. Identify the touched area: task lists/load_task, command generation, AutoML
   runner, trajectory retrieval, metafeature calculation, ASLib assembly,
   selector/portfolio data, or submodule import boundary.
2. Run parser/help checks for any edited command-line script.
3. Use the dry helper to build a small explicit command plan. Prefer one known
   classification task and one known regression task only when network/runtime is
   approved.
4. If changing ASLib schema writing, create or inspect a tiny generated directory
   and verify the seven final files listed in the metadata workflow reference.
5. If changing selector/portfolio files, inspect metric names, strategy names,
   strategy-to-portfolio filename agreement, and cache-key implications.
6. Run focused pytest selectors only after warning about OpenML and bounded
   AutoML runtime.
7. Inspect `git status --porcelain` after tests. Remove temporary working
   directories, cache output, and generated metadata unless the user intends to
   commit them.

## Formatting and static checks

The contributor guide recommends development installs with test/doc/example
extras, then:

```bash
make format
make check
pre-commit run --all-files
```

Use these only if the project tooling and dependencies are available. For a
small metadata-only change, it is acceptable to scope equivalent checks to the
edited files first, then widen before handoff.

## Dirty tree handling

Metadata workflows create many files under the chosen working directory and may
copy trimmed AutoML output. Tests can also leave temporary data if interrupted.
Before handoff:

```bash
git status --porcelain
```

Treat unexpected generated files as a failure signal. Either delete them,
explain why they are intentionally retained, or ask the user whether to keep
them. Do not silently commit broad generated metadata from an experimental run.
