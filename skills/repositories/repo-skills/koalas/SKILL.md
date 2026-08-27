---
name: koalas
description: "Use Koalas, the legacy pandas API on Apache Spark, for DataFrame,
  Spark I/O, SQL, options, plotting, and migration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Koalas repo skill

Use this skill when a task involves legacy Databricks Koalas (`databricks.koalas`), the pandas-like API backed by Apache Spark. Koalas is maintenance-mode software: for Spark 3.2 and newer, prefer `pyspark.pandas` unless the user must keep existing Koalas 1.x code.

## Before you act

1. Read [repository provenance](references/repo-provenance.md) when you need to decide whether this skill is current for a checkout.
2. Read [setup and compatibility](references/setup-and-compatibility.md) before installing, importing, or diagnosing Spark/PyArrow/Python version issues.
3. Use [cross-cutting troubleshooting](references/troubleshooting.md) for import, Java, Spark session, Arrow, optional dependency, and migration failures.
4. For a tiny environment probe, run [scripts/koalas_smoke_check.py](scripts/koalas_smoke_check.py) with `--mode import`, `--mode options`, `--mode dataframe`, or `--mode all`.

## Install and import baseline

```bash
# Conda is usually safest for legacy Python/Spark/PyArrow combinations.
conda install -c conda-forge koalas

# Pip package; add [spark] if PySpark is not already installed.
pip install "koalas[spark]"
```

Minimal import check:

```python
import databricks.koalas as ks
print(ks.__version__)
```

A useful local Spark smoke run normally needs Java, PySpark, compatible pandas/numpy/pyarrow, and early environment settings such as `SPARK_LOCAL_IP=127.0.0.1`, `PYARROW_IGNORE_TIMEZONE=1`, and matching `PYSPARK_PYTHON` / `PYSPARK_DRIVER_PYTHON` when workers otherwise pick another Python.

## Route by task

### Core pandas-like DataFrame work

Use [core-dataframes](sub-skills/core-dataframes/SKILL.md) for:

- Creating `DataFrame`, `Series`, and `Index` objects.
- Migrating pandas snippets with `ks.from_pandas`, `ks.range`, `ks.concat`, `ks.merge`, `ks.melt`, `ks.get_dummies`, `ks.to_datetime`, and `ks.date_range`.
- Indexing, dtype conversion, missing data, string/datetime/categorical accessors, basic statistics, and pandas API gaps.
- Deciding whether a `to_pandas()` collection is bounded and safe.

### Spark interop, I/O, SQL, and storage

Use [spark-io-sql](sub-skills/spark-io-sql/SKILL.md) for:

- `to_spark`, Spark `DataFrame.to_koalas`, explicit `index_col`, and `.spark` accessors.
- `read_csv`, `read_parquet`, `read_json`, `read_delta`, `read_table`, `read_spark_io`, `read_sql*`, `read_orc`, and corresponding writers.
- Spark SQL with `ks.sql`, JDBC databases, Spark catalog tables, Delta/File format setup, plan inspection, checkpoint/cache/repartition/hints, and path semantics.

### Apply, GroupBy, and windows

Use [apply-groupby-window](sub-skills/apply-groupby-window/SKILL.md) for:

- Choosing between `apply`, `transform`, `koalas.apply_batch`, `koalas.transform_batch`, and Series batch transforms.
- Adding return type hints to avoid schema inference and extra Spark jobs.
- `GroupBy.apply`, `GroupBy.transform`, `agg`/`aggregate`, `ks.NamedAgg`, reductions, rolling, expanding, and groupby rolling/expanding.
- Troubleshooting length mismatch, operations on different frames, slow groupby apply, or single-partition window behavior.

### Options, plotting, extensions, and optional integrations

Use [configuration-extensions](sub-skills/configuration-extensions/SKILL.md) for:

- `ks.options`, `get_option`, `set_option`, `reset_option`, and `option_context`.
- Default index type, operations on different frames, shortcut limits, ordered head, and plotting row/sample caps.
- Plotly/Matplotlib backends, custom accessor registration, `.koalas` accessor orientation, MLflow wrapper use, and PySpark 3.2+ migration warnings.

## Operating rules

- Treat Koalas as distributed even when the API looks like pandas. Avoid unbounded `to_pandas()`, `to_numpy()`, Python iteration, plotting, Excel/HTML export, or full-result equality checks.
- Preserve indexes intentionally when crossing Spark boundaries. Prefer `index_col` on Spark-to-Koalas reads/conversions and on Koalas-to-Spark/file writes.
- Configure Spark sessions, Java, Arrow, JDBC jars, Delta extensions, object-store connectors, and executor Python settings before the first Koalas action starts Spark.
- Do not install all extras by default. Install only the needed optional dependency: `koalas[plotly]`, `koalas[matplotlib]`, `koalas[mlflow]`, or a Spark/JDBC/Delta connector required by the task.
- When PySpark is 3.2 or newer and no legacy constraint exists, recommend migration to `pyspark.pandas` and validate behavior changes instead of expanding old Koalas code.
