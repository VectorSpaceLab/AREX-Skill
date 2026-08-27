# Grid Search API Reference

This reference covers the search-time surface only: installation, import, CLI, Python signature, and the column-typing heuristics that drive search setup.

## Install and import notes

`automl_gs` is lightweight, but it does **not** bundle the framework backend. Install the package plus the backend you plan to search:

- `pip install -e .` or `pip install automl_gs`
- `xgboost` for XGBoost searches
- `tensorflow` for TensorFlow searches

The package re-exports the main entry point:

```python
from automl_gs import automl_grid_search
```

Known-good verification from the inspection environment used an editable install plus `pandas==1.5.3` and `tqdm==4.64.1`. Treat later pandas/tqdm upgrades as compatibility changes, not guaranteed drop-ins.

## CLI contract

The CLI accepts positional CSV and target arguments, and the parser also exposes the same names as optional flags. The help contract should include:

- `csv_path`
- `target_field`
- `target_metric`
- `framework`
- `model_name`
- `num_trials`
- `split`
- `num_epochs`
- `gpu`
- `tpu_address`

Typical calls:

```bash
automl_gs data.csv target
automl_gs data.csv target --framework xgboost --num_trials 10
```

Use `automl_gs -h` as the smoke contract for this sub-skill.

## Python signature

Verified public signature:

```python
automl_grid_search(
    csv_path,
    target_field,
    target_metric=None,
    framework='tensorflow',
    model_name='automl',
    context='standalone',
    num_trials=100,
    split=0.7,
    num_epochs=20,
    col_types={},
    gpu=False,
    tpu_address=None,
)
```

### Parameter notes

| Parameter | Meaning | Notes |
| --- | --- | --- |
| `csv_path` | Local CSV path to load. | Use an absolute path when the file is not next to the launch directory. The training subprocess resolves relative paths from the per-trial folder, and it also chooses `python3`/`python` from `PATH`, so a non-activated environment can launch the wrong interpreter. |
| `target_field` | Name of the target column. | Must exist in the CSV header. |
| `target_metric` | Trial-ranking metric. | If omitted, it is inferred from the target type. If you override it, choose a metric that the selected problem-type callback actually emits. |
| `framework` | Search backend. | `tensorflow` is the default; `xgboost` is the fast tabular baseline. |
| `model_name` | Output prefix. | Becomes the prefix for the timestamped best-model folder. |
| `context` | Internal execution context. | Leave at the default for normal CLI/API use. Generated scripts use a special internal context during automl-gs training. |
| `num_trials` | Count of unique hyperparameter samples. | Each trial renders a fresh training script and runs it in a subprocess. |
| `split` | Train fraction. | Passed through to the generated training script. |
| `num_epochs` | Epoch or boosting-round budget. | TensorFlow interprets this as epochs; XGBoost interprets it as boosting rounds. |
| `col_types` | Manual type overrides. | Python-only. Valid values: `text`, `categorical`, `numeric`, `datetime`, `ignore`. |
| `gpu` | GPU toggle for non-TensorFlow frameworks. | For XGBoost, this switches the tree method to GPU hist. |
| `tpu_address` | TPU host for TensorFlow. | Only relevant to TensorFlow runs. |

## Target and input inference

The search phase inspects the first 100 rows of the CSV, then infers the problem type, target metric, and input types from the sampled frame.

### Target problem-type heuristic

The target column drives automatic problem selection:

- exactly 2 unique target values -> `binary_classification`
- pandas dtype `float64` -> `regression`
- everything else -> `classification`

The default ranking metric then follows the problem type:

- regression -> `mse`
- classification / binary classification -> `accuracy`

Override `target_metric` only when you want to rank trials by a different emitted metric.

### Input typing heuristics

The search phase inspects the first 100 rows of the CSV, then infers input types from the sampled frame.

| Rule | Inferred type |
| --- | --- |
| `col_types[field]` is provided | Use the explicit override. |
| field name is `id`, `uuid`, `guid`, `pk`, or `name` | `ignore` |
| pandas dtype is `datetime64[ns]` | `datetime` |
| pandas dtype is `float64` | `numeric` |
| object column with average spaces >= 2.0 | `text` |
| unique values <= 10 | `categorical` |
| pandas dtype is `int64` | `numeric` |
| unique values > 0.9 * row count | `ignore` |
| anything else | `categorical` |

Notes:

- Object columns are passed through `pd.to_datetime(errors='ignore')` before final inference, so date-like strings can become datetimes.
- Low-cardinality numeric codes are commonly misread as categorical; override them with `col_types`.
- If the first 100 rows are not representative, set `col_types` explicitly before blaming the search space.

## Smoke expectations

A healthy search-time setup should satisfy all of the following:

1. `from automl_gs import automl_grid_search` succeeds in the active environment.
2. `automl_gs -h` lists the CLI arguments above.
3. `automl_grid_search(...)` accepts the verified signature and can be called with a local CSV.
4. The current environment's `PATH` resolves the same interpreter that imported `automl_gs`, or the trial subprocess may use a different Python.
5. A tiny XGBoost run can complete without network access.

Use [troubleshooting](troubleshooting.md) if any of those checks fail.
