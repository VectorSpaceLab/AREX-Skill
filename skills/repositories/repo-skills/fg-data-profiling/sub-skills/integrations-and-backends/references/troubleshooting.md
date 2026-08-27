# Integrations and Backends Troubleshooting

## Java or PySpark missing

Symptom: Spark readiness helper reports missing Java or missing `pyspark`.

Recovery:
- Install or activate a Java runtime.
- Install `pyspark` and the package's `spark` extra in the same environment.
- Retry the readiness helper before constructing a Spark `ProfileReport`.

Do not claim Spark support from a CPU-only pandas import.

## Spark local binding failures

If Spark cannot bind locally, set local binding variables in the job:

```bash
export SPARK_LOCAL_IP=127.0.0.1
export SPARK_LOCAL_DIRS=/tmp/fg-spark
```

Then rerun the readiness helper or Spark smoke test.

## Time-series on Spark

`tsmode=True` is not supported for Spark DataFrames. If a user needs time-series
analysis, convert the data to pandas first or route the task to a pandas
workflow.

## Notebook widgets show plain text

Install the notebook extra and verify widget frontend support. If the frontend
still renders text, use `to_notebook_iframe()` or plain HTML export.

## Great Expectations caveat

If `to_expectation_suite()` raises `ImportError`, the dependency is missing.
The current public docs also warn that the full integration is no longer
supported in current versions. Offer JSON or description-based quality outputs
instead.

## Legacy import migration

If a user still imports `ydata_profiling`, the package should work with a
warning. For future code and docs, switch to `data_profiling` and the current
CLI name.
