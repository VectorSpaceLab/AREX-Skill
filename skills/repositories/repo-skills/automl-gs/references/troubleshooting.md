# Cross-Cutting Troubleshooting

Use this page for install, import, environment, and route-selection failures that apply across the whole `automl-gs` package.

## Package import failures

### `ModuleNotFoundError: pkg_resources`

Cause: `setuptools` is missing from the environment, so the package cannot import `pkg_resources`.

Fix:

- Install or repair `setuptools` in the same environment as `automl_gs`.
- Re-run the editable install after the bootstrap package is present.

### Pandas / NumPy binary compatibility

Symptoms:

- Importing `pandas` fails with an ABI or binary-compatibility error.
- Importing `automl_gs` fails early because the pandas import chain is broken.

Fix:

- Reinstall `numpy` and `pandas` together in the same environment.
- Avoid mixing incompatible wheel/conda builds for the same stack.
- If you need a close reproduction of the verified inspection baseline, `pandas 1.5.x` with `numpy 1.26.x` was compatible.

### `tqdm` private-symbol import failure

`automl_gs.utils_automl` imports a private helper from `tqdm._utils`.
A newer tqdm release can remove or relocate that internal symbol.

Symptoms:

- Import fails even though `tqdm` itself is installed.
- The failure points at `_term_move_up` or another private tqdm path.

Fix:

- Pin `tqdm` to a version compatible with the source tree.
- The verified inspection baseline used `tqdm 4.64.x`.
- If you must use a newer tqdm, update the code to stop depending on the private helper.

### `df.dtypes.iteritems()` future compatibility

`automl_gs.automl_gs` still calls `df.dtypes.iteritems()`, which raises a deprecation warning on newer pandas and will disappear in a future pandas release.

Symptoms:

- Search runs emit a pandas FutureWarning before the first trial starts.
- A later pandas major release may turn the warning into a hard failure.

Fix:

- Refresh the code to use `df.dtypes.items()`.
- Until that refresh lands, keep the inspection environment on a pandas 1.x build that still accepts the old access pattern.

## Backend mismatches

### Missing backend package

The core package does not bundle the framework backend.

- XGBoost search requires `xgboost` in the active environment.
- TensorFlow search requires `tensorflow` in the active environment.

Fix:

- Install the backend before running the search.
- Re-run the bundled install smoke after the backend import succeeds.

### The wrong Python launches in the search subprocess

The search loop resolves `python3` or `python` with `shutil.which()`, so a non-activated environment can launch the system interpreter instead of the one that imported `automl_gs`.

Symptoms:

- The parent import works, but the trial subprocess fails with `ModuleNotFoundError` for `pandas`, `xgboost`, or another dependency.
- The generated trial folder starts, then crashes before `metadata/results.csv` is written.

Fix:

- Put the intended environment's `bin/` directory first on `PATH`.
- When writing a wrapper, prepend `Path(sys.executable).parent` to `PATH` before calling `automl_grid_search`.
- Re-run the smoke helper after confirming the subprocess resolves the same interpreter.

## CLI and search-loop problems

### `automl_gs -h` fails

Cause: the package is not installed in the active environment, or a dependency import is broken.

Fix:

- Re-run [scripts/check_install.py](../scripts/check_install.py).
- Repair the import failure before retrying the CLI.

### The search picks the wrong problem type or metric

Cause: the first 100 rows are not representative, or the target column is being parsed differently from what you expected.

Fix:

- Inspect the first 100 rows and override `col_types` when needed.
- Use `grid-search` troubleshooting for the detailed heuristic rules.

### The search writes a folder but the generated model does not behave as expected

Cause: you are now in the generated-artifact workflow, not the search workflow.

Fix:

- Switch to [generated-artifacts](../sub-skills/generated-artifacts/SKILL.md).
- Use the generated-folder troubleshooting guide for `train`/`predict` failures.
