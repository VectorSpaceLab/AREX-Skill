---
name: core-dataframes
description: "Create and manipulate Koalas DataFrame, Series, and Index objects
  with pandas-like APIs and conversion guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Koalas core DataFrames router

Use this sub-skill when the task is about creating, converting, indexing, reshaping, cleaning, typing, or summarizing Koalas `DataFrame`, `Series`, and `Index` objects with pandas-like APIs.

## Handle here

- Constructors and conversion: `databricks.koalas as ks`, `ks.DataFrame`, `ks.Series`, `ks.Index`, `ks.from_pandas`, `ks.range`, `to_pandas`, and `to_spark(index_col=...)` when the focus is preserving or avoiding a default index.
- Top-level dataframe functions: `ks.concat`, `ks.merge`, `ks.melt`, `ks.get_dummies`, `ks.to_datetime`, `ks.date_range`, `ks.isna` / `isnull` / `notna` / `notnull`, and `ks.to_numeric`.
- Selection and indexing: `df[...]`, attribute column access when safe, `loc`, `iloc`, `at`, `iat`, `head`, `tail`, `where`, `mask`, `query`, `set_index`, and `reset_index`.
- Core object APIs: dtype inspection and `astype`, missing-data operations, string accessor `Series.str`, datetime accessor `Series.dt`, categorical accessor `Series.cat`, index and MultiIndex basics, and descriptive statistics.
- Pandas migration decisions: when a pandas snippet can be translated directly, when duplicate/case-sensitive/reserved columns must be fixed, and when `to_pandas()` is acceptable only for bounded data.

## Route elsewhere

- Spark sessions, storage formats, Spark SQL, readers/writers, `.spark` accessor depth, JDBC, and production Spark IO: [spark-io-sql](../spark-io-sql/SKILL.md).
- `apply`, `transform`, `map_in_pandas`, `groupby`, rolling, expanding, window, and return type-hint depth: [apply-groupby-window](../apply-groupby-window/SKILL.md).
- Koalas options, plotting, custom accessors/extensions, optional dependencies, and global performance switches: [configuration-extensions](../configuration-extensions/SKILL.md).

## Operating references

1. Start with [API reference](references/api-reference.md) for supported constructors, methods, signatures, and known API gaps.
2. Use [workflows](references/workflows.md) for concrete migration, creation, conversion, indexing, reshape, dtype, missing, string, datetime, categorical, and statistics recipes.
3. Use [troubleshooting](references/troubleshooting.md) for unsupported pandas APIs, duplicate/case-sensitive columns, reserved `__column__`-style names, pandas collection risks, non-iterability, default-index cost, and dtype gotchas.
4. For a safe runtime probe, run [scripts/koalas_dataframe_quickstart.py](scripts/koalas_dataframe_quickstart.py) with `--check import`, `--check dataframe`, or `--check all`.

## Default decision rules

- Keep data in Koalas/Spark for distributed work; use `to_pandas()` only after a bounded `head`, sample, filter, or other proof that the result fits driver memory.
- Prefer `ks.from_pandas(pdf)` for migration tests and tiny fixtures. For Spark interop, preserve an index with `to_spark(index_col="...")` and `sdf.to_koalas(index_col="...")` when an existing column can serve as the index.
- Reject or rename duplicate columns, case-only duplicate columns such as `a`/`A`, and names wrapped in double underscores before relying on selection or Spark conversion.
- For pandas code that iterates over a `Series` or expects local arrays, rewrite to Koalas vectorized APIs or explicitly collect with `to_numpy()` / `to_pandas()` after bounding data size.
