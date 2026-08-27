# Nullity Utility API Reference

## When to read

Read this for exact behavior of `missingno.nullity_filter` and
`missingno.nullity_sort`, including edge cases that affect plotting APIs.

## Verified signatures

```python
msno.nullity_filter(df, filter=None, p=0, n=0)
msno.nullity_sort(df, sort=None, axis='columns')
```

Both functions return pandas `DataFrame` objects derived from the input frame.
They do not mutate the original DataFrame in normal pandas usage.

## `nullity_filter`

### Inputs

| Parameter | Meaning |
| --- | --- |
| `df` | pandas `DataFrame` whose columns are filtered by non-null counts. |
| `filter` | `"top"`, `"bottom"`, or `None`. Unsupported values fall through as a no-op in this snapshot. |
| `p` | Completeness ratio threshold in `[0, 1]` by convention; source does not enforce the range. |
| `n` | Maximum number of columns selected by count ordering when nonzero. |

### `filter="top"`

Source-backed order:

1. If `p` is nonzero, keep columns whose `df.count(axis="rows") / len(df)` is
   greater than or equal to `p`.
2. If `n` is nonzero, keep the `n` columns with highest non-null counts among
   the current columns.
3. Preserve original column order after selecting the top indices.

Example:

```python
filtered = msno.nullity_filter(df, filter="top", p=0.75, n=5)
```

This means "columns at least 75% complete, capped to the five most complete
columns."

### `filter="bottom"`

Source-backed order:

1. If `p` is nonzero, keep columns whose completeness ratio is less than or
   equal to `p`.
2. If `n` is nonzero, keep the `n` columns with lowest non-null counts among the
   current columns.
3. Preserve original column order after selecting the bottom indices.

Example:

```python
filtered = msno.nullity_filter(df, filter="bottom", p=0.6, n=10)
```

This means "columns at most 60% complete, capped to the ten least complete
columns."

### No-op cases

- `filter=None` returns the input DataFrame unchanged.
- `filter="top"` or `filter="bottom"` with both `p=0` and `n=0` returns the
  input DataFrame unchanged.
- Unsupported `filter` strings are not explicitly rejected by this source; they
  fall through unchanged. Validate user inputs in wrappers if silent no-op would
  be dangerous.

## `nullity_sort`

### Inputs

| Parameter | Meaning |
| --- | --- |
| `df` | pandas `DataFrame` to sort. |
| `sort` | `"ascending"`, `"descending"`, or `None`. Other values raise `ValueError`. |
| `axis` | `"columns"` or `"rows"`. Other values raise `ValueError`. |

### Behavior

- `sort=None` returns the input DataFrame unchanged.
- `axis="columns"` sorts rows by `df.count(axis="columns")`, i.e. the number of
  non-null values in each row.
- `axis="rows"` sorts columns by `df.count(axis="rows")`, i.e. the number of
  non-null values in each column.
- `sort="ascending"` places lower completeness first.
- `sort="descending"` places higher completeness first.

Examples:

```python
# Least complete rows first.
rows = msno.nullity_sort(df, sort="ascending", axis="columns")

# Most complete columns first.
cols = msno.nullity_sort(df, sort="descending", axis="rows")
```

## Plot API use of utilities

| Plot API | Filtering | Sorting |
| --- | --- | --- |
| `matrix` | `nullity_filter(df, filter, n, p)` | `nullity_sort(..., sort, axis="columns")` |
| `bar` | `nullity_filter(df, filter, n, p)` | `nullity_sort(..., sort, axis="rows")` |
| `heatmap` | `nullity_filter(df, filter, n, p)` | `nullity_sort(..., sort, axis="rows")`, then constant-nullity columns are dropped |
| `dendrogram` | `nullity_filter(df, filter, n, p)` | no utility sort before clustering |

## Validation notes

If an agent writes a wrapper around these utilities, validate `filter`, `p`, and
`n` before calling `missingno` when silent no-op or out-of-range thresholds would
surprise the user. The package itself validates `sort` and `axis`, but not
`filter` or `p` range.
