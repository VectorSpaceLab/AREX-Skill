# Core Modin pandas workflows

## Minimal migration

```python
# import pandas as pd
import modin.pandas as pd

df = pd.read_csv("input.csv")
result = df.groupby("category")["value"].sum()
```

For a script rather than a notebook, set the execution engine before importing Modin and put executable distributed work under a main guard:

```python
import os
os.environ.setdefault("MODIN_ENGINE", "Ray")
os.environ.setdefault("MODIN_CPUS", "4")


def main():
    import modin.pandas as pd
    df = pd.read_csv("input.csv")
    print(df.groupby("category")["value"].sum().modin.to_pandas())


if __name__ == "__main__":
    main()
```

Use the Dask route the same way; running Dask work from stdin or top-level unguarded code can trigger Python multiprocessing spawn errors.

## Correctness-first porting pattern

1. Build a tiny fixture that captures representative dtypes, missing values, dates, categorical columns, and edge rows.
2. Run the original pandas code and the Modin port on the same fixture.
3. Normalize sort order and indexes before comparing when the workflow is parallel or partitioned.
4. Compare floats with tolerance and compare dtypes strictly only when downstream code depends on exact dtype.
5. Promote the pattern to production only after materialization points and default-to-pandas warnings are understood.

Example:

```python
import pandas
import modin.pandas as pd

fixture = pandas.DataFrame({"group": ["a", "a", "b"], "value": [1, 2, 3]})
expected = fixture.groupby("group")["value"].sum().sort_index()
actual = pd.DataFrame(fixture).groupby("group")["value"].sum().modin.to_pandas().sort_index()
pandas.testing.assert_series_equal(actual, expected, check_dtype=False)
```

## Read CSV with explicit schema

Parallel CSV reading can infer types per partition. Give `dtype`, `parse_dates`, and `index_col` explicitly when a column has heterogeneous values or when stable index semantics matter.

```python
import modin.pandas as pd

df = pd.read_csv(
    "events.csv",
    dtype={"event_id": "string", "user_id": "string", "amount": "float64"},
    parse_dates=["event_time"],
)
df = df.set_index("event_id")
```

If the workflow only needs a few columns, pass `usecols`. If a non-CSV format defaults to pandas, decide whether serial read plus distribution is acceptable or route to I/O guidance for a parallel alternative.

## Common DataFrame operations

- `concat` works best when combining many similarly shaped Modin objects. Do not repeatedly convert to pandas inside the loop.
- `groupby`/`agg` is the main scalable pattern for reductions. Validate column names after multiple aggregations because pandas-style MultiIndex columns can surprise downstream code.
- `merge`/`join` can benefit from range partitioning for some sorted/keyed workloads; route configuration tuning to the engine sub-skill.
- `apply` may execute Python functions on partitions. Prefer vectorized operations where available and ensure functions are deterministic, pickleable, and do not depend on mutable global state.
- `head`, `tail`, `sample`, and small `to_pandas()` calls are useful for inspection, but full materialization should be explicit.

## Performance measurement

The first operation may include engine startup. For realistic timing, run a tiny warmup first, measure an operation after the engine is initialized, and record the engine/backend/resource settings. Compare to pandas on the same fixture or data sample only after ensuring the task is not dominated by setup, network, or disk I/O.

## Bundled smoke

`taxi_groupby_smoke.py` adapts a Modin taxi example into a local, deterministic fixture. It validates Modin against pandas for CSV parsing, date handling, filters, groupby aggregation, and a derived value. It is safe to run without network or repository files.
