# Vaex analytics reference

This reference covers Vaex statistics, groupby/binby grids, sorting, joins, cardinality tools, and validation patterns for DataFrames that already exist. Route DataFrame creation to `../dataframe-core/SKILL.md`, data export/import to `../io-conversion/SKILL.md`, grid visualization to `../visualization-jupyter/SKILL.md`, and ML pipelines to `../ml-pipelines/SKILL.md`.

## Core statistics

Most DataFrame statistics accept column names, expression strings, or expression objects. Many also support `binby`, `limits`, `shape`, `selection`, `delay`, and `progress`.

Verified signatures:

```python
DataFrame.count(expression=None, binby=[], limits=None, shape=128,
                selection=False, delay=False, edges=False, progress=None,
                array_type=None)
DataFrame.mean(expression, binby=[], limits=None, shape=128,
               selection=False, delay=False, progress=None, edges=False,
               array_type=None)
DataFrame.sum(expression, binby=[], limits=None, shape=128,
              selection=False, delay=False, progress=None, edges=False,
              array_type=None)
DataFrame.std(expression, binby=[], limits=None, shape=128,
              selection=False, delay=False, progress=None, array_type=None)
DataFrame.minmax(expression, binby=[], limits=None, shape=128,
                 selection=False, delay=False, progress=None)
DataFrame.correlation(x, y=None, binby=[], limits=None, shape=128,
                      sort=False, sort_key=np.abs, selection=False,
                      delay=False, progress=None, array_type=None)
DataFrame.percentile_approx(expression, percentage=50.0, binby=[],
                            limits=None, shape=128,
                            percentile_shape=1024,
                            percentile_limits='minmax', selection=False,
                            delay=False, progress=None)
DataFrame.mutual_information(x, y=None, dimension=2, mi_limits=None,
                             mi_shape=256, binby=[], limits=None,
                             shape=128, sort=False, selection=False,
                             delay=False)
```

Expression shortcuts include `df.x.mean()`, `df.x.sum()`, `df.x.std()`, `df.x.minmax()`, `df.x.unique()`, and `df.x.value_counts()`.

### Typical statistics recipes

```python
# Scalars / small arrays.
rows = df.count()
non_nan_x = df.count('x')
mean_xy = df.mean(['x', 'y'])
std_x = df.x.std()
min_x, max_x = df.minmax('x')
p10, p50, p90 = df.percentile_approx('score', [10, 50, 90])

# Correlation and mutual information.
r_xy = df.correlation('x', 'y')
corr_matrix = df.correlation(['x', 'y', 'z'])
corr_pairs = df.correlation([['x', 'y'], ['x', 'z']])  # returns a DataFrame with x/y/correlation columns
mi_xy = df.mutual_information('x', 'y')
mi_matrix = df.mutual_information(x=['x', 'y', 'z'])

# Repeated subset stats via selections.
df.select(df.quality == 'good', name='good')
good_mean = df.mean('score', selection='good')
multi_counts = df.count('score', selection=[None, 'good', df.score > 0])
```

Approximate percentiles and mutual information are grid-based. Increase `percentile_shape`/`mi_shape` or tighten `percentile_limits`/`mi_limits` when precision matters and the result is still affordable.

## Binby grids

`binby` computes statistics on a regular grid without materializing all rows. Use it for histograms/heatmaps or any binned statistic; route actual plotting to `../visualization-jupyter/SKILL.md`.

```python
# One-dimensional count grid.
counts = df.count(binby='x', limits=[0, 100], shape=50)

# Mean y in x bins.
mean_y_by_x = df.mean('y', binby='x', limits=[0, 100], shape=50)

# Two-dimensional grid. The returned array shape follows the binby dimensions.
mean_z_xy = df.mean('z', binby=['x', 'y'], limits=[[0, 10], [-5, 5]], shape=(64, 32))

# Edge bins include underflow/overflow when supported by the aggregation.
counts_with_edges = df.count('*', binby='x', limits=[0, 100], shape=50, edges=True)
```

Grid checklist:

1. Match `limits` nesting to the number of `binby` expressions (`[lo, hi]` for one dimension; `[[lo1, hi1], [lo2, hi2]]` for two).
2. Match `shape` to dimensions (`shape=64` for one dimension; `shape=(64, 32)` for two).
3. Use `limits='minmax'`, a percentage string such as `'90%'`, or explicit limits depending on user intent.
4. Validate a tiny grid first (`shape=4`) before running large multi-dimensional grids.
5. If the user wants a figure, pass the grid or equivalent `df.viz.*` call to `../visualization-jupyter/SKILL.md`.

## Groupby tables

Signature:

```python
DataFrame.groupby(by=None, agg=None, sort=False, ascending=True,
                  assume_sparse='auto', row_limit=None, copy=True,
                  progress=None, delay=False)
```

Basic patterns:

```python
import vaex

# Immediate DataFrame result.
summary = df.groupby(
    by='animal',
    agg={'age': 'mean', 'cuteness': ['mean', 'std']},
    sort=True,
)

# Named aggregate columns with vaex.agg.
summary = df.groupby(
    by='animal',
    agg={
        'rows': vaex.agg.count(),
        'mean_age': vaex.agg.mean('age'),
        'unique_cuteness': vaex.agg.nunique('cuteness'),
        'min_cuteness': vaex.agg.min('cuteness'),
    },
    sort=True,
)

# GroupBy object then aggregate.
grouped = df.groupby(['segment', 'region'], sort=True, ascending=[True, False])
summary = grouped.agg({'revenue_sum': vaex.agg.sum('revenue')})

# Aggregation-specific selections.
summary = df.groupby(
    by='segment',
    agg={
        'mean_score_all': vaex.agg.mean('score'),
        'mean_score_valid': vaex.agg.mean('score', selection='score >= 0'),
        'count_valid': vaex.agg.count(selection=df.score >= 0),
    },
)
```

Useful `vaex.agg` signatures:

```python
vaex.agg.count(expression='*', selection=None, edges=False)
vaex.agg.sum(expression, selection=None, edges=False)
vaex.agg.mean(expression, selection=None, edges=False)
vaex.agg.std(expression, ddof=0, selection=None, edges=False)
vaex.agg.var(expression, ddof=0, selection=None, edges=False)
vaex.agg.min(expression, selection=None, edges=False)
vaex.agg.max(expression, selection=None, edges=False)
vaex.agg.first(expression, order_expression=None, selection=None, edges=False)
vaex.agg.nunique(expression, dropna=False, dropnan=False, dropmissing=False,
                 selection=None, edges=False)
vaex.agg.list(expression, selection=None, dropna=False, dropnan=False,
              dropmissing=False, edges=False)
```

### Missing values, categories, and sorting

- Groupby includes null/missing groups by default. In sorted string groupby results, missing values are placed last.
- Numeric NaN groups are represented as NaN and commonly sort last.
- `value_counts(dropna=True)` drops NaN and missing values; `dropnan=True` and `dropmissing=True` separate those controls.
- Categorized columns can preserve category labels; `vaex.groupby.GrouperCategory(...)` gives explicit category grouping when needed.
- Use `sort=True` and `ascending=` for deterministic output in assertions or reports.
- Use `row_limit=` as a guardrail for high-cardinality grouping. Vaex raises `RowLimitException` when the number of unique groups/combinations reaches the limit.

### Difficult case: derived virtual column with missing categories

```python
import vaex

# Derived column is lazy.
df['net'] = df.revenue - df.cost

# Missing segment values are kept as their own group by default.
summary = df.groupby(
    by='segment',
    agg={
        'rows': vaex.agg.count(),
        'net_sum': vaex.agg.sum('net'),
        'unique_regions': vaex.agg.nunique('region', dropmissing=True),
    },
    sort=True,
    row_limit=10_000,
)

# Validate that missing groups are present or intentionally dropped.
segments = summary.segment.tolist(i1=0, i2=min(10, len(summary)))
```

If the user expects Pandas-like `dropna=True`, explicitly drop or filter missing keys before grouping, or use `value_counts(dropna=True)` for counts.

## Binby to xarray-style grids

Vaex also exposes `df.binby(...)` for labeled binned aggregation results when xarray is available in the environment:

```python
ar = df.binby(by=['x', 'y'], agg={'count': vaex.agg.count()}, sort=True)
# ar.dims and ar.coords describe statistic/key dimensions.
```

Use `df.groupby` for tabular group summaries and `df.count/mean/sum(..., binby=...)` for dense numeric grids. Use `df.binby` when labels/dimensions are important and the environment supports the result type.

## Unique values and value counts

Signatures:

```python
DataFrame.unique(expression, return_inverse=False, dropna=False,
                 dropnan=False, dropmissing=False, progress=False,
                 selection=None, axis=None, delay=False, limit=None,
                 limit_raise=True, array_type='python')
Expression.unique(dropna=False, dropnan=False, dropmissing=False,
                  selection=None, axis=None, limit=None,
                  limit_raise=True, array_type='list', progress=None,
                  delay=False)
Expression.value_counts(dropna=False, dropnan=False, dropmissing=False,
                        ascending=False, progress=False, axis=None,
                        delay=False)
```

Patterns:

```python
keys = df.unique('category', dropna=True, limit=100_000)
vc = df.category.value_counts(dropna=False)
vc_ascending = df.category.value_counts(dropna=True, ascending=True)

# Diagnose key cardinality before a groupby or join.
if len(df.unique('key', dropna=True, limit=100_001, limit_raise=False)) > 100_000:
    raise ValueError('key has too many unique values for this planned workflow')
```

`value_counts` returns a Pandas Series. For high-cardinality columns, treat the result itself as potentially large.

## Joins and sorting

Verified join and sort signatures:

```python
DataFrame.join(other, on=None, left_on=None, right_on=None, lprefix='',
               rprefix='', lsuffix='', rsuffix='', how='left',
               allow_duplication=False, prime_growth=False,
               cardinality_other=None, inplace=False)
DataFrame.sort(by, ascending=True)
```

Join semantics:

- `how='left'` is the default; `how='right'` and `how='inner'` are supported. Full/outer joins are not supported.
- If no `on`, `left_on`, or `right_on` is provided, Vaex joins by row index and adds columns.
- The right side is indexed internally and right columns are referenced through lookup arrays; this avoids copying all right-column data into the left table.
- Right-side duplicate keys are rejected by default because they duplicate left rows. Use `allow_duplication=True` only after confirming that row multiplication is intended and affordable.
- Column name collisions require prefixes/suffixes (`rprefix`, `rsuffix`, `lprefix`, `lsuffix`) unless the collision is the join key.
- Joins ignore filters because filters can change; call `.extract()` on a filtered DataFrame first when the join must use only currently filtered rows.
- Missing/unmatched right values evaluate as masked/null values in the joined DataFrame.

Patterns:

```python
# Left join on the same key name.
joined = left.join(right, on='id', rsuffix='_right')

# Different key names.
joined = left.join(right, left_on='customer_id', right_on='id', rprefix='dim_')

# Inner join.
matched = left.join(right, on='id', how='inner', rsuffix='_right')

# Intentionally allow right-key duplicates after diagnosis.
right_counts = right.key.value_counts(dropna=False)
# Inspect right_counts.head()/known small result before enabling duplication.
joined = left.join(right, on='key', allow_duplication=True)

# Sort result; missing/nan/NA values go to the end regardless of direction.
ordered = joined.sort(['segment', 'score'], ascending=[True, False])
```

### Difficult case: large right table without materializing/copying it

1. Keep both sides as Vaex DataFrames. Do not call `right.to_pandas_df()`, `right.values`, or `np.array(right)`.
2. Check only key cardinality and duplicate risk using Vaex operations:

```python
right_key_counts = right.key.value_counts(dropna=False)
# If this result is too large, sample/limit or group with row_limit before printing.
```

3. If duplicate right keys are accidental, deduplicate/aggregate the right table first (for example, group by key and aggregate one row per key). If duplicates are required, estimate output row count before `allow_duplication=True`.
4. Use prefixes/suffixes to prevent collisions and perform a bounded validation:

```python
joined = left.join(right, on='key', rprefix='right_')
preview = joined.evaluate(['key', 'right_value'], i1=0, i2=5)
```

## Analytic validation patterns

### Validate groupby totals

```python
summary = df.groupby('segment', agg={'rows': vaex.agg.count()}, sort=True)
assert int(summary.rows.sum()) == int(df.count())
```

### Validate binned counts against total rows

```python
counts = df.count(binby='x', limits=[0, 10], shape=10)
inside = int(counts.sum())
total = int(df.count())
assert inside <= total  # rows outside limits are excluded unless edge bins are used
```

### Validate join cardinality

```python
joined = left.join(right, on='key', rprefix='right_')
assert len(joined) == len(left)  # expected for left join without duplicate right keys
matched = joined.count('right_value')
```

### Validate strings/datetimes/accessors before aggregation

```python
df['month'] = df.timestamp.astype('datetime64[ns]').dt.month
df['norm_name'] = df.name.str.strip().str.lower()
assert len(df.evaluate(['month', 'norm_name'], i1=0, i2=5)) == 2
summary = df.groupby(['month', 'norm_name'], agg='count', row_limit=100_000)
```

## Delayed execution for combined passes

Many statistics accept `delay=True` and return promises. Use this when several stats should be scheduled and executed together.

```python
count_task = df.count('score', delay=True)
mean_task = df.mean('score', delay=True)
df.execute()
count = count_task.get()
mean = mean_task.get()
```

Do this only when it simplifies a user workflow; ordinary scalar calls are clearer for small tasks.
