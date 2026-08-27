---
name: configuration-extensions
description: "Configure Koalas options, plotting, custom accessors, optional
  MLflow integration, migration, and performance settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# configuration-extensions

Use this sub-skill when a Koalas task involves package-level configuration, plotting backends, optional plotting or MLflow dependencies, custom accessors/extensions, `.koalas` or `.spark` accessor orientation, PySpark 3.2+ migration, or performance settings controlled by options.

## Route here for

- `ks.options`, `ks.get_option`, `ks.set_option`, `ks.reset_option`, and `ks.option_context`.
- Option selection for performance, display, default indexes, operations on different frames, and plotting.
- Plotting backend selection (`plotly`, `matplotlib`, or a custom module) and row/sample controls.
- Optional dependency diagnosis for `plotly`, `matplotlib`, and `mlflow`; use [`scripts/koalas_optional_dependency_check.py`](scripts/koalas_optional_dependency_check.py).
- Custom extension decorators: `register_dataframe_accessor`, `register_series_accessor`, and `register_index_accessor`.
- Orientation between built-in `.koalas` and `.spark` accessors without deep-diving into their routed API areas.
- `databricks.koalas.mlflow.load_model` and `PythonModelWrapper` usage.
- Maintenance-mode guidance and migration toward `pyspark.pandas` on PySpark 3.2+.

## Route elsewhere

- General `DataFrame`, `Series`, `Index`, pandas-like manipulation, conversion, and indexing: [`../core-dataframes/SKILL.md`](../core-dataframes/SKILL.md).
- Spark IO, SQL, table/file storage, JDBC, and detailed Spark interoperability: [`../spark-io-sql/SKILL.md`](../spark-io-sql/SKILL.md).
- `apply`, `transform`, batch UDF, groupby, rolling, and expanding workflows: [`../apply-groupby-window/SKILL.md`](../apply-groupby-window/SKILL.md).

## Operating checklist

1. Check whether the runtime is legacy Koalas or PySpark 3.2+; for PySpark 3.2+, prefer the built-in pandas API on Spark (`import pyspark.pandas as ps`) unless the user must keep legacy Koalas.
2. Use lower-case dotted option names exactly as listed in the option catalog; unknown or mistyped option names raise an option error.
3. Use `option_context` for temporary settings, especially plotting backend, `compute.default_index_type`, and `compute.ops_on_diff_frames`.
4. For slow default-index or large-plan symptoms, inspect with `kdf.spark.explain(...)`, prefer explicit index columns or distributed default indexes, and consider checkpointing.
5. For plotting or MLflow failures, diagnose the single optional dependency needed before installing broad extras.
6. For detailed recipes and failure recovery, read [`references/configuration-plotting-extensions.md`](references/configuration-plotting-extensions.md) and [`references/troubleshooting.md`](references/troubleshooting.md).
