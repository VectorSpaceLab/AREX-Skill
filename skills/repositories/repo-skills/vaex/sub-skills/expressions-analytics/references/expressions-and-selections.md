# Vaex expressions, virtual columns, selections, and accessors

This reference assumes a Vaex DataFrame named `df` already exists. For creating/opening DataFrames, route to `../dataframe-core/SKILL.md`; for export/import, route to `../io-conversion/SKILL.md`.

## Mental model

- `df.x`, `df['x']`, and `df.col.x` are `Expression` objects, not NumPy arrays.
- Arithmetic, comparisons, boolean logic, many NumPy ufuncs, string/date/struct accessors, and registered functions build new lazy expressions.
- Vaex evaluates expressions in chunks for statistics, groupby/binby, filtering, plotting, and export. Eager APIs such as `.values`, `.to_numpy()`, `.tolist()`, `np.array(df)`, and `to_pandas_df()` create memory-resident results.
- A virtual column stores an expression in the DataFrame metadata and is computed on demand; it is not materialized unless a user explicitly materializes/exports through other workflows.

## Expression creation and safe evaluation

| Need | Vaex pattern | Notes |
| --- | --- | --- |
| Access normal column | `expr = df.x` or `df['x']` | Attribute access only works for identifier-like names that do not collide with accessors/functions. |
| Access non-identifier column | `expr = df['column with spaces']` | Use this form in expressions and aggregations: `df.groupby('group with space', agg=[vaex.agg.sum(df['long name'])])`. |
| Build lazy math | `expr = np.sqrt(df.x**2 + df.y**2)` | NumPy ufuncs return Vaex expressions when used on Vaex expressions. |
| Validate a formula | `df.evaluate(expr, i1=0, i2=5)` | Bounded evaluation catches parse/type/name errors without evaluating the whole dataset. |
| Evaluate in chunks | `for i1, i2, chunk in df.evaluate_iterator(expr, chunk_size=100_000): ...` | Use for custom bounded validation; prefer built-in stats for analytics. |
| Return a small Python list | `expr.tolist(i1=0, i2=5)` | Only for tiny previews or assertions. |

Useful signatures verified from the installed package:

```python
DataFrame.evaluate(expression, i1=None, i2=None, out=None, selection=None,
                   filtered=True, array_type=None, parallel=True,
                   chunk_size=None, progress=None)
Expression.evaluate(i1=None, i2=None, out=None, selection=None,
                    parallel=True, array_type=None)
```

### Expression hygiene checklist

1. Use expression objects (`df.x`) or strings (`'x + y'`) consistently. Prefer objects when column names are unusual.
2. For non-identifier names, never write `df.evaluate('column with spaces + 1')`; use `df.evaluate(df['column with spaces'] + 1)`.
3. For quick validation, evaluate only the first few rows and compare against a NumPy/Pandas calculation on the same tiny slice.
4. If an expression will be reused, add a virtual column; if it is one-off, pass the expression directly to a statistic or groupby aggregator.

## Virtual columns

| Pattern | Example | When to use |
| --- | --- | --- |
| Assignment shorthand | `df['speed'] = np.sqrt(df.vx**2 + df.vy**2)` | Most feature engineering and analytic derived columns. |
| Explicit add | `df.add_virtual_column('score', '2*x + y')` | When the expression is built as a string or when you need `unique=True`. |
| Overwrite safely | `df['x'] = df.x + 1` | Vaex renames the old physical column internally and exposes the new virtual column as `x`; avoid this unless intentional. |
| Use in analytics | `df.groupby('group', agg={'mean_speed': vaex.agg.mean('speed')})` | Virtual columns behave like normal columns for statistics and groupby. |

Signature:

```python
DataFrame.add_virtual_column(name, expression, unique=False)
```

Virtual columns save memory but may be slower than physical columns for repeated heavy calculations. If the user asks to materialize or persist a derived dataset, route to `../io-conversion/SKILL.md` for export/import guidance.

## Selections and filters

Selections mark rows for repeated statistics without copying data. Filters return a DataFrame view that behaves more like Pandas filtering and is useful for downstream operations on a narrowed dataset.

```python
# Named selections for repeated subset stats.
df.select(df.x < 0)                         # default selection
mean_selected = df.mean('y', selection=True)
count_many = df.count('x', selection=['default', 'x >= 0'])

df.select(df.x >= 0, name='nonnegative')
mean_named = df.mean('y', selection='nonnegative')

# Modes combine with the existing selection.
df.select(df.y > 10, mode='and')            # replace/and/or/xor/subtract are supported

# Filtering creates a lazy filtered view; it does not copy rows.
dff = df[df.x < 0]
dff2 = dff.filter(dff.y > 0, mode='and')
```

Signatures:

```python
DataFrame.select(boolean_expression, mode='replace', name='default', executor=None)
DataFrame.filter(expression, mode='and')
```

Use selections for plotting/statistics over several subsets in one pass. Use filtered DataFrames when subsequent operations should see only rows matching the predicate. For joins, remember that Vaex joins ignore filters unless you explicitly call `.extract()` on the filtered DataFrame first; see [analytics-reference.md](analytics-reference.md#joins-and-sorting).

## String expressions

String columns are typically Arrow string columns. String operations are lazy and exposed through `expr.str`.

Common operations:

```python
df['clean_name'] = df.name.str.strip().str.lower()
df['has_alpha'] = df.text.str.contains('alpha', regex=False)
df['prefix'] = df.code.str.slice(0, 3)
df['token_count'] = df.text.str.count(' ', regex=False) + 1
counts = df.clean_name.value_counts(dropna=True)
```

Installed accessor methods include `contains`, `count`, `endswith`, `startswith`, `find`, `replace`, `split`, `join`, `len`, `lower`, `upper`, `strip`, `slice`, `get`, `match`, `extract_regex`, `capitalize`, `title`, and padding/justification helpers.

Null/missing string rules:

- `df.count(df.string_col)` counts non-missing values; `df.count()` counts rows.
- `value_counts(dropna=False)` keeps NaN/null/missing categories; `dropna=True` drops both NaN and missing values.
- Some operations differ from Pandas for null strings and Arrow-backed arrays. Validate a null-containing sample with `expr.evaluate(i1=0, i2=...)` before applying a new operation to large data.

## Datetime and timedelta expressions

Datetime accessors are exposed through `expr.dt`; timedelta arithmetic works with NumPy `timedelta64` values.

```python
df['timestamp'] = df.timestamp_string.astype('datetime64[ns]')
df['month'] = df.timestamp.dt.month
df['hour'] = df.timestamp.dt.hour
df['date_label'] = df.timestamp.dt.strftime('%Y-%m-%d')
df['elapsed_hours'] = (df.end_time - df.start_time) / np.timedelta64(1, 'h')
recent = df[df.timestamp >= np.datetime64('2024-01-01')]
```

Installed `dt` methods/properties include `year`, `month`, `day`, `hour`, `minute`, `second`, `dayofweek`, `dayofyear`, `weekofyear`, `quarter`, `halfyear`, `is_leap_year`, `floor`, `date`, `day_name`, `month_name`, and `strftime`.

Prefer nanosecond (`datetime64[ns]`), microsecond, millisecond, or second resolution for Pandas-backed datetime accessors. Some day-resolution arrays can fail inside Pandas conversion used by `dt` methods; cast first (`expr.astype('datetime64[ns]')`) if needed.

## Struct expressions

Struct arrays support field access through `expr.struct` or bracket notation:

```python
# Given a struct column named payload with fields score and label:
df['score'] = df.payload.struct.get('score')
df['label'] = df.payload[:, 'label']
df['small_payload'] = df.payload.struct.project(['score'])
```

Use struct accessors to avoid expanding large nested columns eagerly. Validate projected fields on a small slice before using them as groupby keys.

## Geo and coordinate accessors

Vaex core exposes a DataFrame-level `df.geo` accessor for coordinate expressions and virtual columns. Typical public methods include `spherical2cartesian`, `cartesian2spherical`, `cartesian_to_polar`, `project_aitoff`, `project_gnomic`, `inside_polygon`, `inside_polygons`, `bearing`, and velocity transforms.

```python
# Adds virtual coordinate columns by default when inplace=True.
df.geo.spherical2cartesian('ra', 'dec', 'distance', 'x', 'y', 'z', inplace=True)
df['inside_roi'] = df.geo.inside_polygon(df.ra, df.dec, polygon_x, polygon_y)
```

Geo helpers operate on expressions and are appropriate for analytic filtering, selections, and derived columns. Route FITS/TAP/astro file opening to `../io-conversion/SKILL.md` and visualization of sky/heatmap outputs to `../visualization-jupyter/SKILL.md`.

## Expression validation recipes

### Derived virtual column before groupby

```python
import numpy as np
import vaex

df['gross_margin'] = (df.revenue - df.cost) / df.revenue
preview = df.evaluate(df.gross_margin, i1=0, i2=min(5, len(df)))
assert len(preview) <= 5

summary = df.groupby(
    by='segment',
    agg={
        'rows': vaex.agg.count(),
        'mean_margin': vaex.agg.mean('gross_margin'),
        'missing_revenue': vaex.agg.count(selection=df.revenue.isna()),
    },
    sort=True,
)
```

### Named selection for repeated statistics

```python
df.select((df.score >= 0) & (df.score <= 1), name='valid_score')
stats = {
    'rows_all': df.count(),
    'rows_valid': df.count(selection='valid_score'),
    'mean_valid': df.mean('score', selection='valid_score'),
    'p95_valid': df.percentile_approx('score', 95, selection='valid_score'),
}
```

### Tiny parity check against NumPy

```python
expr = df.x * 2 + df.y
sample = df.evaluate(expr, i1=0, i2=10)
xs = df.evaluate('x', i1=0, i2=10)
ys = df.evaluate('y', i1=0, i2=10)
np.testing.assert_allclose(sample, xs * 2 + ys)
```

Keep such assertions in user scripts or external review cases, not in runtime skill Markdown.
