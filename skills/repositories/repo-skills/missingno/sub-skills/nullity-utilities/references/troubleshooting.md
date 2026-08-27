# Nullity Utility Troubleshooting

## `sort` raises `ValueError`

Symptom:

```text
ValueError: The "sort" parameter must be set to "ascending" or "descending".
```

Likely cause: `sort` was not `None`, `"ascending"`, or `"descending"`.

Recovery:

```python
msno.nullity_sort(df, sort="ascending")
msno.nullity_sort(df, sort="descending")
msno.nullity_sort(df, sort=None)
```

If the value comes from user input, validate it before calling `missingno`.

## `axis` raises `ValueError`

Symptom:

```text
ValueError: The "axis" parameter must be set to "rows" or "columns".
```

Likely cause: `axis` was not `"rows"` or `"columns"`.

Recovery:

- Use `axis="columns"` to sort rows by the number of non-null values across
  columns.
- Use `axis="rows"` to sort columns by the number of non-null values down rows.

The axis names follow pandas count-axis conventions, so they can feel reversed
from the natural-language target.

## `filter="top"` or `filter="bottom"` returns fewer columns than expected

Likely causes:

- `p` thresholding happens before `n` capping.
- The threshold excludes columns before the numeric cap is applied.
- Ties are selected according to NumPy argsort behavior and then returned in
  original column order for selected indices.

Recovery:

1. Inspect completeness ratios:
   ```python
   completeness = df.count(axis="rows") / len(df)
   print(completeness.sort_values())
   ```
2. Relax `p`, increase `n`, or use only one of the two constraints.
3. Explain that `n` is a maximum, not a guarantee, when `p` removes columns.

## Unsupported `filter` value silently does nothing

In this snapshot, `nullity_filter` explicitly branches only on `"top"` and
`"bottom"`. Other non-`None` values fall through and return the current frame.

Recovery:

- Validate wrapper inputs against `{None, "top", "bottom"}`.
- If a user expected an error, explain that this package version does not raise
  one for unsupported filter strings.

## Out-of-range `p` behaves strangely

The documentation describes `p` as a ratio in `[0, 1]`, but the source does not
validate that range. Values below 0 or above 1 may select every column or no
columns depending on `filter`.

Recovery: validate `0 <= p <= 1` in user-facing wrappers and examples.

## Plot becomes empty after filtering

Symptoms:

- A downstream plot errors or renders nothing after `filter`, `p`, and `n` are
  applied.
- A heatmap has too few variables after filtering and constant-column removal.

Recovery:

1. Check `filtered.shape` before plotting.
2. Reduce the strictness of `p` or increase/remove `n`.
3. For heatmap specifically, remember that all-full and all-empty columns are
   removed after filtering because they have zero nullity variance.
4. Use `bar` or `matrix` if the user needs to display all-full/all-empty columns.

## `axis="columns"` sorted rows instead of columns

This is expected. The implementation counts non-null values along columns for
each row, then reorders rows. To sort columns, use `axis="rows"`.

```python
# Sort rows.
msno.nullity_sort(df, sort="ascending", axis="columns")

# Sort columns.
msno.nullity_sort(df, sort="ascending", axis="rows")
```
