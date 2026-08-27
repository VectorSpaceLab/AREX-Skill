# Nullity Utility Workflows

## When to read

Read this for direct recipes using `nullity_filter` and `nullity_sort`, and for
choosing the same parameters when they are passed through plotting functions.

## Build a tiny mental model

`missingno` utilities work on non-null counts:

```python
counts_by_column = df.count(axis="rows")
completeness = counts_by_column / len(df)
```

Use `top` for columns with higher completeness and `bottom` for columns with
lower completeness.

## Keep least-complete columns for inspection

```python
import missingno as msno

least_complete = msno.nullity_filter(df, filter="bottom", n=10)
```

Use this before `matrix`, `bar`, `heatmap`, or `dendrogram` when a wide
DataFrame is unreadable and the task is to focus on columns with missingness.
Equivalent plot shorthand:

```python
msno.matrix(df, filter="bottom", n=10)
```

## Keep columns above a completeness threshold

```python
mostly_complete = msno.nullity_filter(df, filter="top", p=0.9)
```

This keeps columns whose non-null ratio is at least 90%. Combine with `n` to
cap output width:

```python
mostly_complete = msno.nullity_filter(df, filter="top", p=0.9, n=5)
```

Thresholding occurs before the numeric cap.

## Drill into sparse columns by threshold and cap

```python
sparse = msno.nullity_filter(df, filter="bottom", p=0.5, n=20)
```

This keeps columns at most 50% complete and then caps to the twenty least
complete columns among those that remain.

## Sort rows by row completeness

```python
least_complete_rows_first = msno.nullity_sort(df, sort="ascending", axis="columns")
most_complete_rows_first = msno.nullity_sort(df, sort="descending", axis="columns")
```

Use row sorting before a nullity matrix when you want missing rows grouped at the
top or bottom. `matrix(sort="ascending")` applies this row sort internally.

## Sort columns by column completeness

```python
least_complete_columns_first = msno.nullity_sort(df, sort="ascending", axis="rows")
most_complete_columns_first = msno.nullity_sort(df, sort="descending", axis="rows")
```

Use column sorting before bar or heatmap views when variable order should reflect
completeness. `bar(sort=...)` and `heatmap(sort=...)` apply this internally.

## Combine with visualizations

```python
# Ten least-complete columns, missing rows grouped first.
ax = msno.matrix(df, filter="bottom", n=10, sort="ascending")

# Completeness ranking for columns at least 75% complete.
ax = msno.bar(df, filter="top", p=0.75, sort="descending")

# Correlation among the 30 least-complete columns.
ax = msno.heatmap(df, filter="bottom", n=30)
```

Route users to the visualization sub-skill when the question becomes about
labels, sparklines, correlation interpretation, dendrogram clusters, axes,
figure saving, or matplotlib behavior.

## Verify expected behavior with a tiny frame

```python
import numpy as np
import pandas as pd
import missingno as msno

df = pd.DataFrame({
    "A": [0, np.nan, np.nan],
    "B": [0, 0, np.nan],
    "C": [0, 0, 0],
})
assert list(msno.nullity_filter(df, filter="top", n=1).columns) == ["C"]
assert list(msno.nullity_filter(df, filter="bottom", n=1).columns) == ["A"]
```

The root smoke helper bundles similar assertions without needing the original
repository tests.
