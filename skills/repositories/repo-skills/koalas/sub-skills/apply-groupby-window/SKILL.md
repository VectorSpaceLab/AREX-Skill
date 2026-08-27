---
name: apply-groupby-window
description: "Apply, transform, groupby aggregation, and rolling or expanding
  window workflows for Koalas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Apply, GroupBy, And Window Workflows

Use this sub-skill when a Koalas task needs custom higher-order computation, pandas UDF-style batch functions, grouped aggregation, or rolling/expanding windows.

## Route Here For

- Choosing between `DataFrame.apply`, `DataFrame.transform`, `DataFrame.koalas.apply_batch`, `DataFrame.koalas.transform_batch`, and the deprecated `DataFrame.map_in_pandas` alias.
- `Series.apply`, `Series.map`, `Series.transform`, and `Series.koalas.transform_batch`.
- `GroupBy.apply`, `GroupBy.transform`, `DataFrameGroupBy.agg`/`aggregate`, `ks.NamedAgg`, grouped reductions, cumulative operations, filtering, ranking, `get_group`, and SeriesGroupBy-only helpers.
- `DataFrame.rolling`, `Series.rolling`, `DataFrame.expanding`, `Series.expanding`, plus `groupby(...).rolling(...)` and `groupby(...).expanding(...)`.
- Koalas and pandas return type hints that prevent schema inference and avoid an extra Spark job.

## Route Elsewhere

- Basic DataFrame/Series/Index creation, conversion, indexing, reshaping, dtype, string, datetime, missing-value, and categorical work: [core-dataframes](../core-dataframes/SKILL.md).
- Spark SQL, IO, Spark accessors, `to_spark`, Spark `DataFrame.to_koalas`, and Spark-column-only transforms: [spark-io-sql](../spark-io-sql/SKILL.md).
- Global options and performance settings such as `compute.ops_on_diff_frames`, `compute.shortcut_limit`, default index type, plotting, and extension accessors: [configuration-extensions](../configuration-extensions/SKILL.md). This sub-skill explains where those options affect apply/groupby/window choices.

## Read First

1. For API choice and examples, read [references/apply-groupby-window.md](references/apply-groupby-window.md).
2. For failures and performance symptoms, read [references/troubleshooting.md](references/troubleshooting.md).

## Fast Decision Rules

- Use `transform`/`transform_batch` only when every partition or group returns the same number of rows as it received.
- Use `apply`/`apply_batch` when the result can be shorter, longer, scalar per group, or a new frame shape.
- Prefer built-in grouped reductions or `agg` over `GroupBy.apply` whenever the computation is expressible as named aggregations.
- Add return type hints to any non-trivial apply/transform/batch/groupby function before running it on large or already-shuffled data.
- Treat ungrouped rolling/expanding and global ranking as small-data or carefully validated workflows because they can require single-partition Spark windows.
