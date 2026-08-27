# DataFrame Workflow Recipes

## Start From Pandas Safely

```python
import pandas as pd
import dask.dataframe as dd

pdf = pd.DataFrame({"id": [1, 2, 1], "value": [10, 20, 30]}).set_index("id")
df = dd.from_pandas(pdf, npartitions=2, sort=True)
```

Use `sort=True` when the pandas index can define useful divisions. Use `sort=False` only when preserving row order matters more than indexed partition knowledge.

## Build A Custom Reader With `from_map`

Use `from_map` when every partition can be loaded from a descriptor such as a filename, database range, or API page.

```python
import pandas as pd
import dask.dataframe as dd

parts = ["part-0", "part-1"]
meta = pd.DataFrame({"id": pd.Series(dtype="int64"), "value": pd.Series(dtype="float64")})

def load_part(part):
    return pd.DataFrame({"id": [0], "value": [1.0]})

df = dd.from_map(load_part, parts, meta=meta)
```

Prefer `from_map` over `from_delayed` when the loading pattern is regular because it gives Dask more structure and often clearer metadata behavior.

## Recover From `map_partitions` Metadata Mismatch

When a partition function changes columns, dtypes, index, or series name, pass explicit `meta`.

```python
import pandas as pd

meta = pd.DataFrame({
    "id": pd.Series(dtype="int64"),
    "ratio": pd.Series(dtype="float64"),
})

def add_ratio(part):
    out = part.assign(ratio=part["value"] / part["value"].sum())
    return out[["id", "ratio"]]

result = df.map_partitions(add_ratio, meta=meta)
```

If the function changes the index in a way that invalidates existing divisions, use `clear_divisions=True` or call `.clear_divisions()` where available. Do not leave stale divisions on data that is no longer sorted by the same index.

## Plan Groupby Work

Fast/common cases:

- Built-in reductions: `df.groupby("key").value.mean()`, `sum`, `count`, `std`, `var`, `nunique`.
- Grouping by index or by columns aligned with known divisions.
- Large input reduced to small output, then `.compute()` at the boundary.

Use `split_out=` for high-cardinality grouped outputs:

```python
result = df.groupby("customer_id").amount.sum(split_out=16)
```

Use `dd.Aggregation` when a custom operation can be decomposed into chunk, aggregate, and finalize steps. Avoid arbitrary `groupby.apply` unless it is necessary; it can trigger a shuffle when grouping columns are not aligned with known divisions.

## Plan Joins And Merges

Cheaper joins:

- Dask DataFrame joined to a small pandas DataFrame.
- Large Dask DataFrame joined to a single-partition Dask DataFrame.
- Dask DataFrames joined on known, sorted indexes with `left_index=True` and `right_index=True`.

Expensive joins:

- Large-large joins on non-index columns.
- Joins after divisions have been lost or made unknown.

Workflow for repeated joins:

```python
left = left.set_index("account_id", shuffle_method="tasks")
right = right.set_index("account_id", shuffle_method="tasks")
joined = left.merge(right, left_index=True, right_index=True, how="left")
```

If a shuffle is unavoidable, choose a shuffle method deliberately through `dataframe.shuffle.method` or method-level `shuffle_method` when supported. On distributed clusters, peer-to-peer shuffle may be available; on a single machine, disk/tasks shuffles are common.

## Use Divisions Intentionally

Inspect partition knowledge:

```python
df.npartitions
df.divisions
df.known_divisions
```

Known divisions speed indexed `.loc`, index joins, and some grouped operations. CSV and JSON reads usually start with unknown divisions. Parquet can calculate divisions from metadata with `calculate_divisions=True`, but this may require scanning row-group metadata and can be expensive on remote or very large datasets.

Use `set_index` sparingly because it shuffles. If data is already sorted, pass `sorted=True` and known `divisions` when possible.

## Repartition For Size And Output

Use repartitioning after filters or before writing files:

```python
filtered = df[df.status == "ok"]
filtered = filtered.repartition(npartitions=max(1, filtered.npartitions // 4))
```

For time-indexed data, use frequency-based repartitioning when supported. For memory tuning, estimate partition sizes with `memory_usage_per_partition()` and aim for partitions that fit comfortably in worker memory while avoiding thousands of tiny tasks.

## Categorical Workflows

Dask tracks known and unknown categoricals:

```python
df["kind"] = df["kind"].astype("category")  # usually unknown categories
known = df.categorize(columns=["kind"])
known["kind"].cat.known
```

Use `.categorize(columns=[...])` once for multiple columns when category metadata is required. Use `.cat.as_unknown()` to drop known category metadata without scanning. After Parquet round trips, known categories may become unknown; restore categories only when needed.

## String And PyArrow Handling

Dask may convert object string columns to pyarrow-backed strings depending on `dataframe.convert-string` and dependency availability. If exact dtype behavior matters, set config before importing `dask.dataframe` in a fresh process:

```python
import dask

dask.config.set({"dataframe.convert-string": False})
import dask.dataframe as dd
```

When writing reusable tests or scripts, assert semantic values instead of brittle object/string backend dtypes unless dtype behavior is the point of the task.

## Optimizer-Aware Parquet Workflow

A good analytical pipeline keeps projection and filters visible until compute:

```python
df = dd.read_parquet("dataset", columns=["account", "amount", "ts"], filters=[[('amount', '>', 0)]])
summary = df[df.amount > 100].groupby("account").amount.sum(split_out=8)
result = summary.compute()
```

Avoid persisting immediately after `read_parquet` if later column selection or filtering should push down into IO. Persist after expensive filtering/shuffling only when the full intermediate dataset will be reused.

## Query Plan Inspection

Use text inspection first:

```python
optimized = df.optimize()
optimized.pprint()
```

Use `df.explain()` when Graphviz is available and a visual query plan helps. Explain projection/filter pushdown, partition pruning, automatic partition resizing, and shuffle avoidance in user-facing reviews.
