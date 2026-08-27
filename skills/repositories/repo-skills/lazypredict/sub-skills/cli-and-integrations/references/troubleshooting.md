# CLI and Integration Troubleshooting

## CLI command is not found

**Symptoms:** `lazypredict: command not found`, but Python import may work.

**Recovery:** verify the same Python environment owns both the import and the
console script. Run `python -m pip show lazypredict`, check the environment's
script directory, or reinstall Lazy Predict in the active environment. The
bundled smoke helper can test the CLI command object even when PATH is wrong.

## Target column not found

**Symptoms:** CLI output like `Error: target column 'label' not found` and exit
code `1`.

**Recovery:** inspect the CSV header and pass the exact column name to
`--target`. Beware whitespace, case differences, and files saved with unnamed
index columns.

## CSV parsing or data-type failures

Lazy Predict's CLI reads with pandas and passes all non-target columns as
features. If fitting fails for many models, reproduce the run in Python API form
so you can inspect dtypes, choose a categorical encoder, select a small model
list, and inspect `.errors`.

## CLI is too slow

The CLI does not expose `max_models`, selected model lists, `timeout`, or
`cv`. For a bounded agent workflow, switch to the Python API in the
supervised-benchmarking sub-skill.

## MLflow does not log anything

MLflow tracking activates only when both conditions are true:

1. the `mlflow` package is installed;
2. `MLFLOW_TRACKING_URI` is set in the process environment before constructing
   the Lazy Predict estimator.

If either is missing, Lazy Predict continues without tracking. It does not start
`mlflow ui` for you.

## Dask or PySpark conversion surprises

Auto-conversion can collect distributed data to local pandas/numpy objects.
For large data, validate sample sizes and driver memory before fitting. If the
user wanted Spark-native MLlib estimators, use `LazySparkClassifier` or
`LazySparkRegressor` with a proper Spark runtime instead of auto-converting.

## Spark class import or construction fails

`pyspark` and a JVM/Spark runtime are optional. Install the `spark` extra and
verify Spark separately. Do not treat Spark failures as base Lazy Predict
failures when the user only needs local sklearn-style benchmarking.

## GPU or Intel acceleration is absent

Absence of `sklearnex`, PyTorch CUDA, RAPIDS/cuML, or boosting libraries is
normal for a base install. Use the root environment checker to determine which
optional modules are present, then install only the requested backend's package
set. If CUDA is unavailable, Lazy Predict may warn and fall back to CPU.
