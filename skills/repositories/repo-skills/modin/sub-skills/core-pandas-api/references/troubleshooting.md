# Core pandas API troubleshooting

## Import and engine warnings

Set engine variables before importing Modin. If a script imports `modin.pandas` first and then changes `MODIN_ENGINE`, the first operation may already have fixed the engine. Restart the process after changing engine, backend, CPU count, or partition count.

## Multiprocessing startup failures

Ray and Dask may start workers. In `.py` files, do not execute Modin work at module import time. Use:

```python
def main():
    import modin.pandas as pd
    ...

if __name__ == "__main__":
    main()
```

This is especially important for Dask and for platforms that use spawn-style multiprocessing.

## `defaulting to pandas` warnings

First determine whether correctness is affected. Usually the warning means Modin used pandas for that operation. If data is small, accepting the warning can be reasonable. If data is large or the operation is repeated in a loop, rewrite with supported vectorized operations, isolate that step on a small subset, or use the Native/Pandas backend intentionally.

## CSV dtype or parse surprises

Symptoms include inconsistent integer/string columns, missing-value conversion, object dtypes where numeric dtypes were expected, or comparison failures against pandas. Fix by adding `dtype`, `parse_dates`, `na_values`, and a stable `index_col` or `set_index` step. Compare a tiny fixture before using full data.

## Ordering and index differences

Parallel execution can expose implicit ordering assumptions. Sort by semantic keys before comparing. Reset or preserve indexes deliberately. For groupby aggregations, sort index and compare with `check_dtype=False` unless dtype is a requirement.

## Slow first operation

The first Modin action may initialize Ray or Dask. Warm the engine with a tiny DataFrame before benchmarking. Do not compare pandas and Modin timings that include different network, download, or cache states.

## Memory pressure

Avoid full `to_pandas()` on large data. Use `head`, `sample`, aggregates, row counts, schema checks, or partition-aware writes. If a required pandas-only step must materialize, make it explicit and bounded.

## Function serialization

Custom functions passed to `apply`, groupby UDFs, or partition transformations should be top-level or otherwise pickleable. Avoid closures over large objects, open files, database connections, and mutable global state.
