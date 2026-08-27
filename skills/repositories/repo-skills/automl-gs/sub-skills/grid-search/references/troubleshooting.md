# Grid Search Troubleshooting

Use this page when import smoke checks fail, the trial subprocess crashes, or the search appears to choose the wrong metric or column types.

## Fast triage

1. Confirm the active environment can import the package and the selected backend (`xgboost` or `tensorflow`).
2. Run `automl_gs -h` and confirm the CLI exposes the expected arguments.
3. Check whether the CSV path is local and reachable from the launch directory.
4. If the model type or metric looks wrong, inspect the first 100 rows and the inferred column types.
5. If the trial completed but the best folder looks odd, inspect `automl_results.csv` and `metadata/results.csv` before changing the search settings.
6. If you see a pandas `iteritems` FutureWarning, it is currently noisy but not fatal; the source still uses `df.dtypes.iteritems()` and should be refreshed to `items()` in a future code update.

## Package import failures

### `ModuleNotFoundError: pkg_resources`

Cause: `setuptools` is missing from the environment, so the package cannot load `pkg_resources`.

Fix:

- Install or repair `setuptools` in the same environment as `automl_gs`.
- Re-run the editable install after the bootstrap package is present.

### Pandas / NumPy binary compatibility

Symptoms:

- Importing `pandas` fails with an ABI or binary-compatibility error.
- Importing `automl_gs` fails early because the pandas import chain is broken.

Fix:

- Reinstall `numpy` and `pandas` together in the same environment.
- Avoid mixing pip wheels and conda packages for the same stack.
- If you need a close reproduction of the verified inspection environment, the known-good baseline used `pandas==1.5.3`.

### `tqdm` internal import compatibility

`utils_automl.py` imports `tqdm._utils._term_move_up`, which is a private helper. A newer tqdm release can remove or relocate that internal symbol.

Symptoms:

- Import fails even though `tqdm` itself is installed.
- The failure points at `_term_move_up` or another private tqdm path.

Fix:

- Pin tqdm to a version compatible with the source tree.
- The verified inspection baseline used `tqdm==4.64.1`.
- If you must use a newer tqdm, update the source to stop depending on the private helper.

## Missing framework packages

The core package does not bundle the backend framework.

- XGBoost search requires `xgboost` to be installed in the active environment.
- TensorFlow search requires `tensorflow` to be installed in the active environment.
- The generated search subprocess imports the selected framework, so the parent `automl_gs` import can succeed while the trial later fails.

Fix:

- Install the framework before running the search.
- Re-run the bundled smoke script only after the backend import succeeds.

## Column-type and heuristic surprises

### Low-cardinality numeric columns became categorical

Cause: numeric codes with 10 or fewer unique values are classified as categorical by the heuristic.

Fix:

- Override the column with `col_types={'code_col': 'numeric'}`.
- This is the most common reason a tiny tabular test looks wrong.

### Tiny numeric fixtures can create duplicate quantile bins

Cause: the sampled hyperparameters may choose `numeric_strat='quantiles'` or `numeric_strat='percentiles'`, and repeated numeric values can produce duplicate bin edges in `pd.cut`.

Fix:

- Use a slightly richer fixture with unique or well-spread numeric values.
- If you are only smoke-testing, keep the fixture numeric columns monotonic and diverse.
- If the real dataset has tied values, rerun with a different numeric strategy or let the search sample a different trial.

### Date columns stayed as object or text

Cause: the first 100 rows were not representative, the date strings were mixed-format, or `pd.to_datetime(errors='ignore')` left the column as object.

Fix:

- Normalize the CSV before the search.
- Use `col_types={'created_at': 'datetime'}` when you know the column intent.

### Sparse prose did not become text

Cause: the heuristic looks for average spaces. Short labels with few spaces may fall through to categorical instead of text.

Fix:

- Override with `col_types={'description': 'text'}`.

### ID-like columns should disappear but do not

Cause: only the exact lower-case names `id`, `uuid`, `guid`, `pk`, and `name` are auto-ignored.

Fix:

- Rename or override with `col_types={'legacy_id': 'ignore'}` if the column is a pure identifier.

## CSV and path mistakes

### Relative CSV paths fail in the trial subprocess

Cause: the training subprocess runs from the per-trial folder and resolves the source CSV relative to that location.

Fix:

- Use an absolute `csv_path` when the file is not in the launch directory.
- If you use a relative path, make sure it still works after the subprocess prepends `../`.

### The trial subprocess uses the wrong Python

Cause: `build_subprocess_cmd()` chooses `python3` or `python` with `shutil.which()`, so a non-activated environment may launch the system interpreter instead of the one that imported `automl_gs`.

Fix:

- Run the search from a shell where the intended environment's `bin/` directory is first on `PATH`.
- If you are using a helper script, prepend `Path(sys.executable).parent` to `PATH` before calling `automl_grid_search`.
- Re-run the smoke test after confirming the subprocess resolves the same interpreter.

### The CSV is not local

Cause: automl-gs expects a local file path. It does not download URLs on its own.

Fix:

- Download the CSV first and point the search at the local file.

### The target field is wrong or missing

Symptoms:

- The search crashes when it cannot find the target column.
- The inferred problem type is obviously wrong because the target column was parsed incorrectly.
- XGBoost throws a label or DMatrix error because the target values are non-numeric strings.

Fix:

- Double-check the exact header spelling and case.
- Remove leading/trailing whitespace from the header names before the search.
- Confirm the first 100 rows actually contain both classes for classification.
- For XGBoost, make sure the target values are numeric-compatible or pre-encoded before the search.

### The sample is too small or unbalanced

Symptoms:

- Stratified splits fail or train/validation metrics are meaningless.
- The binary target only has one class in the training window.
- A tiny CSV causes the heuristics to overfit on missing or rare values.

Fix:

- Increase the sample size.
- Rebalance the target.
- Make sure both the train and validation slices contain enough examples of every class.
- If the first 100 rows are a weird slice, reorder or expand the sample before rerunning.

## Metric override surprises

If you override `target_metric`, the best-trial comparison uses the direction defined in `metrics.yml`.

Examples:

- `target_metric='accuracy'` means higher is better.
- `target_metric='log_loss'` means lower is better.

Common mistake: choosing a metric that the shipped callback does not emit for that problem type. In that case, `train_results[target_metric]` cannot be read during result selection.

Fix:

- Use one of the emitted metrics for the selected problem type, or extend the callback first.
- Remember that `reg_objective` is a loss choice, not the ranking metric.

## When to use the smoke script

If you are unsure whether the environment or the code is at fault, run `scripts/run_tiny_xgboost_search.py` in a clean workdir. It creates a local fixture, prepends the current interpreter's `bin/` directory to `PATH`, exercises the Python API, and confirms that `automl_results.csv` plus the timestamped best folder are written.
