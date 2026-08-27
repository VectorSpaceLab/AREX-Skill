---
name: io-interoperability
description: "Use Modin readers, writers, conversion APIs, glob I/O, SQL
  partitioning, and partition handoff safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modin I/O and interoperability

Use this sub-skill when a task needs nontrivial Modin I/O, conversion between Modin and other dataframe systems, experimental multi-file glob I/O, distributed SQL reading, custom text parsing, dataframe interchange, Ray/Dask conversion, or direct partition handoff.

## Start here

1. Read [references/io-reference.md](references/io-reference.md) for stable and experimental readers/writers, async read mode, glob APIs, distributed SQL parameters, and parser dependency caveats.
2. Read [references/interoperability.md](references/interoperability.md) for pandas, NumPy, Arrow, dataframe-interchange, Ray, Dask, `from_map`, `unwrap_partitions`, and `from_partitions` conversions.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a format falls back to pandas, a glob API is unavailable for the selected engine, a conversion requires Ray/Dask, or a parser dependency is missing.
4. Run [scripts/interop_smoke.py](scripts/interop_smoke.py) to validate small pandas/NumPy/interchange/Arrow conversions, with optional Ray/Dask checks.
5. Run [scripts/io_glob_smoke.py](scripts/io_glob_smoke.py) to validate local experimental CSV glob I/O and optional JSON/parquet glob round-trips.

## Routing boundaries

This sub-skill owns:

- Stable `modin.pandas` readers/writers beyond the simplest `read_csv` starter path.
- `MODIN_ASYNC_READ_MODE` consequences for `read_csv`, `read_fwf`, `read_table`, and `read_custom_text`.
- Experimental `modin.experimental.pandas` glob readers/writers and `read_custom_text`.
- Distributed SQL partitioning concepts: `partition_column`, `lower_bound`, `upper_bound`, and `max_sessions`.
- Conversion APIs in `modin.pandas.io`: `from_arrow`, `from_dataframe`, `from_ray`, `from_dask`, `from_map`, `to_pandas`, `to_numpy`, `to_ray`, and `to_dask`.
- Low-level partition APIs in `modin.distributed.dataframe.pandas`: `unwrap_partitions` and `from_partitions`.

Route ordinary pandas-compatible operations to `../core-pandas-api/SKILL.md`, engine/resource setup to `../engines-configuration/SKILL.md`, and experimental frontends such as XGBoost, Batch Pipeline, spreadsheet, Modin NumPy, or Modin Polars to `../advanced-extensions/SKILL.md`.

## Operating pattern

1. Choose and verify the engine first. Experimental glob APIs are Ray/Dask/Unidist-oriented; Ray is the default local smoke route.
2. Validate a tiny local fixture before using remote object stores, SQL databases, or many-file glob patterns.
3. Keep credentials out of code and logs. Use secure runtime configuration for cloud storage and SQL engines.
4. Materialize with `to_pandas()` or `to_numpy()` only on bounded data.
5. For Arrow/Ray/Dask conversion, verify the package dependency and engine compatibility before converting large objects.
6. Use direct partition APIs only when a task truly needs partition ownership; otherwise prefer public readers and conversion helpers.
