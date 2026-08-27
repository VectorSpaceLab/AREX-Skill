---
name: dataframe-workflows
description: "Use this Dask sub-skill for Dask DataFrame creation,
  CSV/Parquet/JSON/SQL IO, partitions and divisions, groupby/aggregation,
  joins/merge, shuffle, repartitioning, categorical/string/pyarrow handling, and
  dask-expr query planning/optimizer behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Dask DataFrame Workflows

Use this sub-skill when a task is about pandas-like tabular workflows with `dask.dataframe` or the `dask_expr` DataFrame implementation.

## Route Here For

- Creating DataFrames with `dd.from_pandas`, `dd.from_map`, `dd.from_delayed`, `dd.from_dask_array`, `dd.read_csv`, `dd.read_parquet`, `dd.read_json`, and SQL readers.
- Planning CSV, Parquet, JSON, ORC, HDF, SQL, cloud-storage, and partitioned dataset reads/writes.
- Reasoning about `npartitions`, `divisions`, `known_divisions`, `set_index`, `repartition`, `shuffle`, and partition sizing.
- Implementing `groupby`, `Aggregation`, `split_out`, joins, merges, index-aware operations, and shuffle-aware query plans.
- Handling `meta`, metadata inference, categorical known/unknown state, pandas/pyarrow string conversion, pyarrow-backed dtypes, and dataframe backends.
- Inspecting or explaining dataframe query planning with `optimize()`, `pprint()`, `explain()`, projection/filter pushdown, partition pruning, and shuffle avoidance.

## Route Elsewhere

- Use `../configuration-diagnostics-cli/SKILL.md` for generic Dask config mechanics, CLI commands, progress bars, profilers, install checks, and scheduler diagnostics.
- Use `../array-workflows/SKILL.md` for Dask Array creation, chunking, blockwise array operations, gufuncs, and array/dataframe conversion details beyond `from_dask_array` or `to_dask_array` routing.
- Use `../bag-bytes-workflows/SKILL.md` for bag-first text/JSON records, bytes, Avro, and object pipelines before conversion to dataframe.
- Use `../core-graphs-schedulers/SKILL.md` for generic task graphs, delayed, `compute`, `persist`, custom collection protocol, and scheduler selection.

## Start With These References

- `references/api-reference.md` for public DataFrame APIs, method selection, signatures, and dask-expr inspection surfaces.
- `references/io-and-data-formats.md` for CSV, Parquet, JSON, SQL, cloud storage, backend dispatch, and format-specific pitfalls.
- `references/workflows.md` for practical workflow recipes covering divisions, joins, groupby, repartitioning, `meta`, categoricals, and optimizer-aware planning.
- `references/troubleshooting.md` for missing dependencies, pyarrow strings, unknown divisions, shuffles, metadata failures, categories, Parquet schema/filter issues, and import-time config.

## Bundled Smoke Scripts

Run these from this sub-skill directory or pass their paths explicitly:

```bash
python scripts/dataframe_smoke.py --help
python scripts/dataframe_smoke.py
python scripts/dataframe_demo_smoke.py --help
python scripts/dataframe_demo_smoke.py
```

The scripts use tiny temporary or in-memory data, public `dask.dataframe` APIs, and local/synchronous computation. They do not depend on repository files or write persistent datasets unless you pass an output path.

## Operating Rules

- Keep dataframe pipelines lazy while defining work; call `.compute()` or `.persist()` only at execution boundaries or in small smoke checks.
- Prefer Parquet for durable tabular datasets; use CSV/JSON for ingestion or interchange when schema and partitioning limits are acceptable.
- Preserve or create useful divisions for repeated `.loc`, index joins, and groupby/apply on the index; avoid unnecessary full-data shuffles.
- Provide explicit `meta` for user functions, custom readers, empty/heterogeneous partitions, or workflows where metadata inference is expensive or wrong.
- Treat `dataframe.query-planning`, `dataframe.convert-string`, and dataframe backend config as import-time-sensitive choices; set them before importing `dask.dataframe` in fresh processes when behavior must be deterministic.
