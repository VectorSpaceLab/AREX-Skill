# Apply, GroupBy, And Window Troubleshooting

## Symptom: `transform` Or `transform_batch` Fails With Length/Shape Errors

Likely cause: the function filters, aggregates, explodes, or otherwise returns a different row count than its input chunk or group.

Recovery:

1. If every input row must have one output row, rewrite the function to return a same-length pandas Series/DataFrame.
2. If output length is intentionally variable, switch from `transform` to `apply`, or from `koalas.transform_batch` to `koalas.apply_batch`.
3. For grouped work, use `GroupBy.transform` only for same-length per-group features; use `GroupBy.apply` for top-k, filtering per group, scalar summaries, or new output shapes.
4. Add explicit return type hints after changing APIs so Koalas does not infer a misleading schema from a small sample.

## Symptom: Apply/Transform Runs Two Spark Jobs Or Starts With A Slow Sampling Job

Likely cause: missing return type hints. Koalas samples up to `compute.shortcut_limit` rows to infer the pandas output schema, then runs the actual Spark job.

Recovery:

- Add a scalar hint for scalar Series functions: `def f(x) -> np.float64: ...`.
- Add a Series hint for same-length output: `def f(pser) -> pd.Series[float]: ...`.
- Add a named DataFrame hint for frame output: `def f(pdf) -> pd.DataFrame["col": float, "flag": bool]: ...`.
- Use an empty pandas sample with `zip(sample.columns, sample.dtypes)` when names and dtypes are generated programmatically.
- If testing inference behavior itself, adjust `compute.shortcut_limit` through [configuration-extensions](../../configuration-extensions/SKILL.md); do not encode global option changes in library-style workflows unless the caller asks.

## Symptom: Output Columns Are Named `c0`, `c1`, ...

Likely cause: the function used an unnamed DataFrame return type such as `pd.DataFrame[int, float]` or `ks.DataFrame[int, float]`.

Recovery:

```python
def f(pdf) -> pd.DataFrame["amount": float, "flag": bool]:
    return pd.DataFrame({"amount": pdf["amount"], "flag": pdf["amount"] > 0})
```

Use named annotations or `zip(sample.columns, sample.dtypes)` when downstream code depends on column names.

## Symptom: Result Lost Its Original Index After A Type-Hinted Apply

Likely cause: Koalas return type hints describe data columns and Spark schema but not the original index. Annotated `apply`, `apply_batch`, and groupby apply/transform paths can attach a default index.

Recovery:

1. Convert important index levels to ordinary columns before applying.
2. Return those columns from the function with explicit names and dtypes.
3. Restore the desired index with normal Koalas DataFrame APIs after the apply result is produced; route detailed index work to [core-dataframes](../../core-dataframes/SKILL.md).
4. Review default-index options in [configuration-extensions](../../configuration-extensions/SKILL.md) for large outputs.

## Symptom: Combining Apply Output With Original Frame Raises Operations-On-Different-Frames Errors

Likely cause: `DataFrame.koalas.apply_batch` and many shape-changing apply paths produce a new DataFrame anchor. Koalas blocks operations across unrelated frames by default because the alignment can require expensive joins.

Recovery:

- If the output is same-length and should align row-for-row with the input, use `DataFrame.koalas.transform_batch` instead of `apply_batch`.
- If a join is semantically required, carry a stable key column through the apply result and join explicitly.
- If the caller deliberately wants automatic alignment between different frames, route the option decision to [configuration-extensions](../../configuration-extensions/SKILL.md) for `compute.ops_on_diff_frames`.

## Symptom: GroupBy Apply Is Slow Or Produces Surprising Index/Schema

Likely causes:

- `GroupBy.apply` is flexible but slower than grouped reductions, `agg`, cumulative methods, or `transform`.
- Missing return hints trigger schema inference.
- Koalas uses internal group-key columns for the grouped-map operation; do not depend on hidden grouping columns being available inside the pandas function.
- Annotated outputs may receive a default index.

Recovery:

1. Replace `apply` with `agg`, `NamedAgg`, a built-in reduction, or `transform` when possible.
2. For `DataFrameGroupBy.apply`, return a pandas DataFrame and annotate as `pd.DataFrame[...]` or `ks.DataFrame[...]`; do not annotate frame-groupby apply as a Series.
3. For `SeriesGroupBy.apply`, choose a scalar hint for scalar per-group results or a Series hint for row-preserving outputs.
4. Put needed group keys into ordinary columns before grouping if the returned result must include them.
5. Sort or reset indexes before comparing to pandas in tests; distributed group order may differ.

## Symptom: GroupBy `agg` Rejects The Specification

Likely causes:

- `DataFrameGroupBy.agg` expects a string, a list of strings, a dict mapping column labels to strings/lists, or keyword relabeling with `(column, aggfunc)` / `ks.NamedAgg`.
- SeriesGroupBy `agg`/`aggregate` is not implemented in this Koalas version; use SeriesGroupBy reductions such as `sum`, `mean`, `nunique`, `value_counts`, or convert to a frame when needed.
- MultiIndex column labels must match the full column-label level.

Recovery:

```python
kdf.groupby("g").agg({"x": ["min", "max"], "y": "sum"})
kdf.groupby("g").agg(x_max=("x", "max"), y_sum=("y", "sum"))
kdf.groupby("g").agg(x_max=ks.NamedAgg(column="x", aggfunc="max"))
```

For SeriesGroupBy, prefer `kdf.groupby("g")["x"].sum()` or `kdf[["g", "x"]].groupby("g").agg({"x": "sum"})`.

## Symptom: Rolling/Expanding Is Very Slow Or Warns About Single Partition

Likely cause: ungrouped rolling/expanding uses Spark windows without a partition specification, which can move all data into one partition. Global `DataFrame.rank` and `Series.rank` have the same single-partition risk.

Recovery:

- Prefer `groupby(...).rolling(...)` or `groupby(...).expanding(...)` when a natural partition key exists.
- Keep ungrouped rolling/expanding for small or bounded data, or run a Spark plan check through [spark-io-sql](../../spark-io-sql/SKILL.md).
- For rank, use grouped rank when semantically correct; otherwise warn the caller that global rank can be expensive.
- Use built-in Spark SQL/window logic through [spark-io-sql](../../spark-io-sql/SKILL.md) for large custom window specifications not covered by Koalas' rolling/expanding methods.

## Symptom: Rolling Or Expanding Results Differ From Pandas Around Nulls Or `min_periods`

Likely cause: Koalas rolling/groupby rolling treats `min_periods` as a fixed-size threshold and counts null values as periods. This differs from pandas behavior in some cases.

Recovery:

1. State the Koalas behavior before promising pandas-identical null semantics.
2. Test edge rows explicitly when `min_periods`, nulls, and group boundaries matter.
3. If exact pandas behavior is required for a small dataset, route conversion trade-offs to [core-dataframes](../../core-dataframes/SKILL.md); for large data, use explicit Spark window expressions through [spark-io-sql](../../spark-io-sql/SKILL.md).

## Symptom: Custom Function Needs Spark Columns Or SQL Instead Of Pandas Objects

Likely cause: apply/groupby/window APIs here pass pandas Series/DataFrame objects to user functions. Spark-column transformations belong to the Spark accessor or Spark SQL layer.

Recovery:

- Use this sub-skill for pandas UDF-style functions.
- Route Spark-column expressions, Spark plans, `to_spark`, `DataFrame.spark.apply`, and SQL/window specifications to [spark-io-sql](../../spark-io-sql/SKILL.md).
