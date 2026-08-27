# Apply, GroupBy, Type-Hint, And Window Guide

This reference distills Koalas 1.8.x behavior for custom pandas-style functions, grouped computations, and windowed statistics. Functions passed to these APIs usually execute inside Spark-backed pandas UDF or grouped-map paths, so the right API and return type hint matter for both correctness and performance.

## Imports Used In Examples

```python
import numpy as np
import pandas as pd
import databricks.koalas as ks
```

Koalas supports both Koalas-style and pandas-style return annotations for many APIs. In newer Koalas, prefer pandas return annotations when the function actually receives and returns pandas objects; Koalas annotations are still accepted in this version.

## Choose The Right Custom-Function API

| Need | Preferred API | Function input | Required output shape | Notes |
| --- | --- | --- | --- | --- |
| Element-wise scalar mapping on one Series | `Series.apply(func)` or `Series.map(func)` | Scalar values inside a pandas Series batch | Same Series length | Use a scalar return hint such as `-> np.int64` or `-> str`. `Series.map(dict)` is convenient for small dictionaries; huge dictionaries can create large Spark expressions. |
| Same-length column-wise DataFrame transform | `DataFrame.transform(func, axis=0)` | pandas Series chunks, one column at a time | Same length as input | `axis=1` is not implemented for `DataFrame.transform`; use `DataFrame.apply(..., axis=1)` for row-wise work. |
| Same-length full-DataFrame batch transform | `DataFrame.koalas.transform_batch(func)` | pandas DataFrame chunk | Same length as input chunk | Can return a DataFrame or Series. Do not mutate the index; index information is retained by the original Koalas object when possible. |
| Variable-length or new-shape full-DataFrame batch output | `DataFrame.koalas.apply_batch(func)` | pandas DataFrame chunk | Any length, DataFrame output | Output is treated as a new DataFrame. If combining it back with the original frame, expect operations-on-different-frames behavior. |
| Row-wise DataFrame work | `DataFrame.apply(func, axis=1)` or `axis="columns"` | pandas Series for each row | Scalar, list-like, Series, or DataFrame-compatible result | Use scalar hints for scalar row output or DataFrame hints for multi-column row output. |
| Column-wise DataFrame work that can change length | `DataFrame.apply(func, axis=0)` | pandas Series chunks | Any length | Do not use for global column aggregations over the complete Series; the function sees internal chunks. |
| Group-wise flexible output | `GroupBy.apply(func)` | pandas DataFrame or Series per group | Any length or scalar depending on groupby type | Flexible but slower than reductions/`agg`/`transform`; use only when those do not express the computation. |
| Group-wise same-length output | `GroupBy.transform(func)` | pandas Series per group/column | Same length per group | Function must return a Series type. Built-in cumulative methods are usually faster. |
| Fixed aggregations per group | `DataFrameGroupBy.agg(...)` / `aggregate(...)` | Built-in aggregate names | One row per group | Supports dicts, lists of function names, tuple relabeling, and `ks.NamedAgg`. |
| Rolling or expanding statistics | `.rolling(...).sum()` etc. or `.expanding(...).mean()` | Spark window expressions | Same object type as caller | Supported methods are `count`, `sum`, `min`, `max`, `mean`, `std`, and `var`. |

Deprecated aliases exist for older code: `DataFrame.apply_batch`, `DataFrame.transform_batch`, and `DataFrame.map_in_pandas` warn and forward to `DataFrame.koalas.apply_batch` or `DataFrame.koalas.transform_batch`. Prefer the `.koalas` namespace in new guidance. Inspected Koalas 1.8.x exposes `Series.koalas.transform_batch`; use `Series.apply`, `Series.map`, or `Series.transform` instead of a nonexistent `Series.koalas.apply_batch`.

## Type Hints And Schema Inference

Without a return annotation, Koalas samples up to `compute.shortcut_limit` rows to infer the output schema. If the frame already has shuffles, sorts, or groupby operations upstream, this can cause two Spark jobs: one for inference and one for the real computation. Add return type hints for production-size data.

### Series Or Element-Wise Hints

Use scalar annotations for element-wise `Series.apply`/`Series.map` functions:

```python
def bucket(x) -> str:
    return "large" if x >= 100 else "small"

kdf["bucket"] = kdf["amount"].apply(bucket)
```

Use `pd.Series[...]` or `ks.Series[...]` for same-length Series outputs passed to transform-style APIs:

```python
def zscore(pser) -> pd.Series[float]:
    return (pser - pser.mean()) / pser.std()

kdf.groupby("account")["amount"].transform(zscore)
```

### DataFrame Hints With Column Names

Plain DataFrame annotations specify types by position and create generated names such as `c0`, `c1`. Prefer named annotations when users need stable output columns:

```python
def add_features(pdf) -> pd.DataFrame["id": int, "amount2": float]:
    return pd.DataFrame({"id": pdf["id"], "amount2": pdf["amount"] * 2.0})

ks.range(5).assign(amount=lambda x: x.id * 1.5).koalas.apply_batch(add_features)
```

Dynamic annotations are also accepted when the output schema matches a pandas object already available to the function definition:

```python
sample = pd.DataFrame({"amount": pd.Series([], dtype="float64"), "flag": pd.Series([], dtype="bool")})

def normalize(pdf) -> pd.DataFrame[zip(sample.columns, sample.dtypes)]:
    return pd.DataFrame({"amount": pdf["amount"] / 100.0, "flag": pdf["amount"] > 0})
```

When a DataFrame-returning function is annotated, Koalas may attach a default index to the result because the type hint does not encode the original index. If the index matters, make it an ordinary column before applying, then restore or reset it explicitly. Configure default-index behavior through [configuration-extensions](../../configuration-extensions/SKILL.md) when needed.

## DataFrame Apply And Batch Patterns

### Same-Length Column Transform

```python
def scale(pser) -> pd.Series[float]:
    return pser.astype("float64") * 2.0

out = kdf[["x", "y"]].transform(scale)
```

Caveat: the Series passed to `DataFrame.transform` is an internal pandas Series chunk, not the whole column. Avoid global aggregations that require every row unless the calculation is safe per chunk or rewritten as a grouped/whole-frame operation.

### Row-Wise Apply

```python
def row_score(row) -> np.float64:
    return row["x"] * 0.7 + row["y"] * 0.3

scores = kdf[["x", "y"]].apply(row_score, axis="columns")
```

For multi-column row output, use a DataFrame return annotation:

```python
def row_features(row) -> pd.DataFrame["sum_xy": float, "diff_xy": float]:
    return pd.Series({"sum_xy": row["x"] + row["y"], "diff_xy": row["x"] - row["y"]})
```

### Whole-Chunk Batch Apply Versus Batch Transform

Use `transform_batch` when the output is row-preserving and should remain aligned with the original frame:

```python
def add_ratio(pdf) -> pd.DataFrame["x": float, "ratio": float]:
    return pd.DataFrame({"x": pdf["x"], "ratio": pdf["x"] / pdf["y"]})

same_length = kdf[["x", "y"]].koalas.transform_batch(add_ratio)
```

Use `apply_batch` when the function filters, explodes, or otherwise changes row count:

```python
def positive_rows(pdf) -> pd.DataFrame["x": float, "y": float]:
    return pdf.loc[pdf["x"] > 0, ["x", "y"]]

filtered = kdf[["x", "y"]].koalas.apply_batch(positive_rows)
```

Because `apply_batch` returns a new DataFrame anchor, combining `filtered` with columns from `kdf` may require enabling operations on different frames. Route that decision to [configuration-extensions](../../configuration-extensions/SKILL.md); do not silently enable it for large data because it can trigger expensive joins.

## Series Apply, Map, Transform, And Batch Transform

- `Series.map(dict)` replaces values using a small mapping. Missing dictionary keys become `None` unless the dictionary implements `__missing__`.
- `Series.map(func)` forwards to `Series.apply(func)`.
- `Series.apply(func, args=..., **kwds)` invokes a scalar function over Series values. A scalar return hint avoids schema inference.
- `Series.transform(func)` is equivalent to `Series.apply(func)` for one function; with a list of functions it returns a DataFrame with one output column per function name.
- `Series.koalas.transform_batch(func)` passes a pandas Series chunk and expects a pandas Series-like same-length result.

Example:

```python
def centered(pser) -> pd.Series[float]:
    return pser - pser.mean()

centered_amount = kdf["amount"].koalas.transform_batch(centered)
```

Again, the batch is not the whole Series. Use grouped transforms, joins against aggregate results, or Spark expressions when correctness requires full-column context.

## GroupBy Aggregation And Reductions

Prefer built-in reductions and aggregations when they express the intent:

```python
summary = (
    kdf.groupby("account")
       .agg(
           amount_max=ks.NamedAgg(column="amount", aggfunc="max"),
           amount_min=ks.NamedAgg(column="amount", aggfunc="min"),
       )
       .sort_index()
)
```

Equivalent tuple relabeling is also supported:

```python
summary = kdf.groupby("account").agg(
    amount_max=("amount", "max"),
    tx_count=("txn_id", "count"),
)
```

Other supported aggregation styles include:

```python
kdf.groupby("account").agg({"amount": "sum", "fee": "mean"})
kdf.groupby("account").agg({"amount": ["min", "max"]})
kdf.groupby("account").agg("sum")
kdf.groupby("account").agg(["min", "max"])
```

Useful grouped reductions and operations include `all`, `any`, `count`, `first`, `last`, `max`, `mean`, `median`, `min`, `nunique`, `size`, `std`, `sum`, `var`, `cumcount`, `cummax`, `cummin`, `cumprod`, `cumsum`, `diff`, `idxmax`, `idxmin`, `fillna`, `bfill`, `ffill`, `head`, `tail`, `shift`, `rank`, and `filter`. SeriesGroupBy also has `nsmallest`, `nlargest`, `value_counts`, and `unique`; DataFrameGroupBy owns `agg`/`aggregate` and `describe` in this version.

Use `as_index=False` only with `DataFrame.groupby`, not `Series.groupby`. Use `dropna` deliberately: `dropna=True` filters null group keys in grouped results, while `dropna=False` keeps them where supported.

## GroupBy Apply And Transform

Use `GroupBy.transform` for same-length, per-group features:

```python
def demean(group_values) -> pd.Series[float]:
    return group_values - group_values.mean()

kdf["amount_demeaned"] = kdf.groupby("account")["amount"].transform(demean)
```

Use `GroupBy.apply` for variable-length or shape-changing per-group output:

```python
def top_two(pdf) -> pd.DataFrame["account": str, "amount": float]:
    return pdf.sort_values("amount", ascending=False).head(2)[["account", "amount"]]

top = kdf.groupby("account").apply(top_two)
```

Rules that prevent common mistakes:

- For frame groupby, a `Series` return type hint is not supported; annotate DataFrame output for `DataFrameGroupBy.apply`.
- For series groupby, scalar or Series outputs are valid depending on whether the function reduces or preserves rows.
- `GroupBy.apply` receives pandas data inside the function, so pandas APIs are allowed there; Koalas operations inside the function are usually the wrong layer.
- Built-in reductions and `agg` are easier for Spark to optimize and should be tried before `apply`.
- Annotated groupby functions can lose the original group index and receive a default index in the result. Preserve group keys as columns or reset/rebuild the index explicitly when downstream code depends on it.

## Rolling And Expanding Windows

Create window objects from DataFrame or Series:

```python
rolling_mean = kdf["amount"].rolling(window=3, min_periods=2).mean()
expanding_sum = kdf[["amount", "fee"]].expanding(min_periods=3).sum()
```

Grouped windows partition by group and return an index that includes group keys:

```python
per_account = kdf.groupby("account")["amount"].rolling(3).sum().sort_index()
```

Supported rolling and expanding methods are `count`, `sum`, `min`, `max`, `mean`, `std`, and `var`. `window` for rolling must be non-negative. `min_periods` must be non-negative. In Koalas rolling/groupby-rolling, `min_periods` behaves as a fixed window-size threshold and null values are counted as periods, unlike some pandas expectations.

Ungrouped rolling and expanding use a Spark window ordered by Koalas' natural row order without a partition specification. That can move data into a single partition. Use grouped windows when possible, check Spark plans through [spark-io-sql](../../spark-io-sql/SKILL.md), and keep ungrouped windows bounded or validated on representative data.

## Performance And Option Touchpoints

- `compute.shortcut_limit` controls how many rows Koalas samples for local shortcut/schema inference. Lowering it can expose distributed behavior during testing, but global option changes belong in [configuration-extensions](../../configuration-extensions/SKILL.md).
- `compute.ops_on_diff_frames` affects combinations between outputs from `apply_batch` and their original frames. Enable only with a clear join/alignment reason.
- Global `DataFrame.rank`/`Series.rank` can use a single partition. Grouped rank partitions by group but still shuffles and orders within groups.
- If a custom function contains side effects, expect execution count to follow Spark jobs and partitions, not local pandas intuition. Avoid side effects in functions passed to Koalas apply/transform APIs.
