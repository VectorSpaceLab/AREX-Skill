# Vaex DataFrame workflows

## Mental model

A Vaex `DataFrame` wraps columnar arrays or file-backed datasets. Columns are exposed as `Expression` objects (`df.x`, `df['x']`, `df.col.x`) and expression operations are lazy: `df.x * 2` builds an expression and does not compute the whole array until an operation asks for results. A virtual column is a named lazy expression stored on the DataFrame. Filtering and slicing create shallow DataFrame views instead of copying all data.

Use eager materialization only for small, intentional checks. For large data, validate with `head`, `shape`, `count`, a short slice, a bounded `evaluate(i1=..., i2=...)`, chunked `evaluate_iterator`, or a real aggregation routed to `../expressions-analytics/SKILL.md`.

## Create a DataFrame

### In-memory arrays or dictionaries

```python
import numpy as np
import vaex

x = np.arange(5)
df = vaex.from_arrays(x=x, y=x ** 2)
# Equivalent when names are dynamic:
df2 = vaex.from_dict({'x': x, 'label': ['a', 'b', 'c', 'd', 'e']})
```

Use this for tests, examples, or data that already fits in memory. All columns must have compatible lengths. Lists are accepted, but explicit NumPy or Arrow arrays make types and missing-value behavior clearer.

### Pandas input

```python
import pandas as pd
import vaex

pdf = pd.DataFrame({'x': [1, 2, 3], 'city': ['a', None, 'c']})
df = vaex.from_pandas(pdf, copy_index=False)
```

`from_pandas` converts an existing eager Pandas object into a Vaex DataFrame; it does not make the upstream Pandas operation lazy. Use it at ingestion boundaries or for small handoff data. If the Pandas index matters, pass `copy_index=True` and choose `index_name`.

### Arrow tables and Vaex datasets

```python
import pyarrow as pa
import vaex

table = pa.table({'x': [1, 2, 3], 's': ['a', None, 'c']})
df = vaex.from_arrow_table(table)
```

Use Arrow-backed columns for strings, nulls, list/struct values, and interoperability. If you already have a Vaex dataset object, wrap it with `vaex.from_dataset(dataset)`.

### Files and examples

```python
import vaex

df = vaex.open('data.hdf5')        # lazy/opened through registered file openers
small_csv = vaex.from_csv('tiny.csv')
example = vaex.example()
```

`vaex.open` is the usual entry for Vaex-optimized files and can lazily open some file types. `vaex.from_csv` reads CSV through the Vaex/Pandas path and can convert or chunk. Keep detailed format, export, conversion, cloud, and plugin questions in `../io-conversion/SKILL.md`.

### Concatenate rows

```python
combined = vaex.concat([df1, df2])
strict = vaex.concat([df1, df2], resolver='strict')
```

Default `resolver='flexible'` fills missing columns with missing values when schemas differ. Use `resolver='strict'` when schema mismatches should fail. If virtual columns differ across inputs, Vaex may materialize or raise depending on the conflict; validate with `get_column_names(virtual=True)` and small bounded checks before concatenating large data.

## Inspect safely

```python
names = df.get_column_names()               # real + virtual, visible columns
real = df.get_column_names(virtual=False)   # physical/source columns only
shape = df.shape                            # (filtered_rows, visible_columns)
preview = df.head(5)                        # shallow DataFrame slice
records = preview.to_records()              # safe for tiny previews
row_count = df.count()                      # count rows without materializing columns
```

Notes:

- `len(df)` and `df.shape[0]` respect active filters. Computing the length of a filtered DataFrame can require a count of the filter mask.
- `head(n)` returns a shallow DataFrame slice, not a Pandas object. Convert only the small preview if needed.
- `get_column_names` has useful filters: `virtual=False`, `hidden=True`, `regex='...'`, `dtype=...`, and `strings=False`.
- Hidden internal or renamed columns usually start with `__` and are excluded unless `hidden=True`.

## Column access and expressions

```python
x = df.x                 # only for valid Python identifiers that do not collide
x2 = df['x']             # always safe for a literal column name
expr = df.x + df.y * 2   # lazy Expression
```

For names with spaces, punctuation, keywords, Unicode, or method/function collisions, prefer brackets:

```python
df = vaex.from_dict({'A-B': [1, 2], 'with space': ['a', None], '#': [3, 4]})
score = df['A-B'] * 10 + df['#']
values = df.evaluate(score, i1=0, i2=2, array_type='python')
```

Vaex can often resolve raw strings like `'A-B'` or `'#'` as column names, but bracket access makes intent unambiguous and avoids parse/`NameError` problems once you combine names into larger expressions.

## Add virtual columns

```python
df['speed'] = (df.vx ** 2 + df.vy ** 2) ** 0.5
# or
df.add_virtual_column('speed', '(vx**2 + vy**2)**0.5')
```

Virtual columns behave like normal columns in `get_column_names`, filtering, selections, and many downstream operations, but they store an expression rather than an eager array. Use virtual columns for Pandas-like derived columns:

```python
# Pandas style: pdf['ratio'] = pdf['sales'] / pdf['visits']
df['ratio'] = df['sales'] / df['visits']
valid = df[df['visits'] > 0]
small_check = valid.evaluate('ratio', i1=0, i2=min(5, len(valid)), array_type='python')
```

If assigning an actual array (`df['new'] = array`), the array must match the unfiltered DataFrame length. Assigning an array with the filtered length is a common mistake; use a virtual expression or assign to a copy built from the correct full-length data.

## Slice, filter, and select

### Slicing

```python
first_100 = df[:100]
last_10 = df[-10:]
subset_columns = df[['x', 'y']]
```

Slicing returns a shallow DataFrame view. `df[['x', 'y']]` returns a shallow copy with selected columns and dependency tracking for virtual columns.

### Filtering

```python
dff = df[df.x > 0]
dff = dff[dff.y < 10]          # narrows further
dff2 = dff.filter(dff.x < -5, mode='or')  # can broaden with OR
```

A filter is attached to the returned DataFrame. It does not copy the underlying data. `df.evaluate('x')` on a filtered DataFrame uses `filtered=True` by default; pass `filtered=False` only when you explicitly want the unfiltered active range.

### Selections

```python
df.select(df.x > 0)                         # default named selection
df.select(df.y < 10, name='low_y')
selected_x = df.evaluate(df.x, selection=True, array_type='python')
selected_count = df.count(selection=True)
low_y_count = df.count(selection='low_y')
```

Selections are useful when the same DataFrame remains intact while you compare subsets, visualize, or compute statistics. A selection name is not the same as a filter; a selection only applies when a method receives `selection=True`, a selection name, or a selection expression.

Selection modes include `replace`, `and`, `or`, `xor`, and `subtract`. Use `df.select(None)` or `df.select_nothing()` to clear a selection.

## Evaluate intentionally

```python
# Small bounded check
sample = df.evaluate(df['with space'], i1=0, i2=10, array_type='python')

# Apply a stored selection
selected = df.evaluate(df.x, selection=True, array_type='numpy')

# Stream larger checks in chunks
for i1, i2, chunk in df.evaluate_iterator(df.x, chunk_size=100_000, array_type='numpy'):
    print(i1, i2, chunk[:3])
```

`evaluate` returns arrays and may require the result to fit in memory. Use it to validate a small sample, to fill an explicitly provided output buffer, or to stream via `evaluate_iterator`. If the real task is mean/sum/count/groupby/binby/value_counts/unique/join/sort, route to `../expressions-analytics/SKILL.md` and use Vaex computations that return compact results.

## Missing values and dtypes

Vaex distinguishes:

- **missing/masked/null**: data is absent; works across dtypes through masked arrays or Arrow nulls.
- **NaN**: a floating-point value representing not-a-number; data is present but invalid or undefined.
- **NA**: union of missing and NaN for convenience.

Useful DataFrame and Expression methods:

```python
df.select_non_missing(column_names=['name'])
clean_missing = df.dropmissing(column_names=['name'])
clean_nan = df.dropnan(column_names=['score'])
clean_na = df.dropna(column_names=['score'])

missing_count = df['name'].countmissing()
nan_count = df['score'].countnan()
na_mask = df['score'].isna()
filled = df['name'].fillmissing('unknown')
```

String columns with `None` are usually Arrow strings with missing values, not `NaN`. Numeric float columns may contain both masked values and `NaN`; choose the method that matches the user's meaning.

## Minimal validation pattern

Use this compact pattern when debugging a user DataFrame:

```python
def inspect_vaex_df(df):
    names = df.get_column_names()
    info = {
        'shape': df.shape,
        'columns': names,
        'real_columns': df.get_column_names(virtual=False),
        'head': df.head(min(5, len(df))).to_records(),
        'row_count': int(df.count()),
    }
    return info
```

Do not add `.values` or full `to_pandas_df()` to a generic validator. Add bounded expression checks only after choosing a few columns and row limits.
