# Spark Backend Reference

## When to read

Read this when a user wants Spark DataFrame profiling, Spark readiness checks,
or help diagnosing a Spark-specific failure.

## Minimum Spark prerequisites

The package's Spark workflow requires:

- `pyspark` installed in the environment;
- a working Java runtime;
- a local Spark configuration that can bind to the loopback address.

The package's CI uses local binding hints such as `SPARK_LOCAL_IP=127.0.0.1`
and `SPARK_LOCAL_DIRS` to keep Spark runs predictable in CI or containerized
hosts.

## Source-verified behavior

- `ProfileReport` can accept a Spark DataFrame when `pyspark` is available.
- The package dynamically imports Spark-specific modules only when PySpark is
  installed.
- Time-series mode is not supported for Spark DataFrames and raises a
  `NotImplementedError`.
- Spark support is documented as available from version 4.0.0 onward in the
  package docs.
- Supported Spark features in the docs: univariate analysis, head/tail sample,
  Pearson and Spearman correlations.
- Missing values, interactions, and improved histogram support are listed as
  not yet complete in the docs.

## Practical workflow

1. Run the readiness script.
2. Confirm Java is visible and PySpark imports.
3. Bind Spark locally if necessary.
4. Construct a small Spark DataFrame from a tiny pandas fixture.
5. Only then profile with `ProfileReport(spark_df)`.

## Readiness script

Use the bundled helper before trying a real Spark profile:

```bash
python scripts/check_spark_readiness.py
```

The helper reports Java availability, `pyspark` import status, and optional
session readiness. It does not install software or download Spark.
