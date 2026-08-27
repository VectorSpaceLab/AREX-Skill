# Visualization API Reference

## When to read

Read this for verified signatures, parameter behavior, return values, and
source-backed implementation notes for `missingno` plotting APIs.

## Verified public signatures

```python
msno.matrix(
    df, filter=None, n=0, p=0, sort=None, figsize=(25, 10),
    width_ratios=(15, 1), color=(0.25, 0.25, 0.25), fontsize=16,
    labels=None, label_rotation=45, sparkline=True, freq=None, ax=None
)

msno.bar(
    df, figsize=None, fontsize=16, labels=None, label_rotation=45,
    log=False, color='dimgray', filter=None, n=0, p=0, sort=None,
    ax=None, orientation=None
)

msno.heatmap(
    df, filter=None, n=0, p=0, sort=None, figsize=(20, 12),
    fontsize=16, labels=True, label_rotation=45, cmap='RdBu',
    vmin=-1, vmax=1, cbar=True, ax=None
)

msno.dendrogram(
    df, method='average', filter=None, n=0, p=0,
    orientation=None, figsize=None, fontsize=16, label_rotation=45, ax=None
)
```

All four functions return a matplotlib `Axes` object. Use `ax.figure` to save or
close the figure.

## Shared parameters

| Parameter | Applies to | Behavior |
| --- | --- | --- |
| `df` | all | A pandas `DataFrame`; nullity is derived from `df.isnull()` / `df.notnull()`. |
| `filter`, `n`, `p` | all | Passed to `missingno.nullity_filter`; read the nullity utilities sub-skill for exact `top`/`bottom` semantics. |
| `sort` | `matrix`, `bar`, `heatmap` | `matrix` sorts rows by row completeness; `bar` and `heatmap` sort columns by column completeness. `dendrogram` filters but does not sort before clustering. |
| `figsize` | all | Matplotlib figure size. Some defaults change with column count or orientation. Ignored for some existing-axis reuse. |
| `fontsize` | all | Label/annotation font scaling. |
| `labels` | matrix/bar/heatmap | Controls column labels or correlation labels. `matrix` defaults to labels for <=50 columns and none for >50; `heatmap` defaults to annotation labels. |
| `label_rotation` | matrix/bar/heatmap/dendrogram | Tick-label rotation. |
| `ax` | all | Reuses an existing matplotlib axis. For `matrix`, a sparkline on an existing axis is not supported; set `sparkline=False` to avoid the warning. |

## `matrix` notes

- Builds an RGB image where present values use `color` and missing values are
  white.
- With `sparkline=True`, a right-side sparkline shows per-row completeness and
  annotates maximum/minimum completeness counts.
- `width_ratios` controls matrix/sparkline width only when the sparkline is
  enabled.
- `freq` adds time ticks only for `PeriodIndex` or `DatetimeIndex`. The function
  raises `KeyError` if the index type is incompatible or if the requested
  frequency cannot be located in the index.
- Labels default to visible for up to 50 columns and hidden for more.

## `bar` notes

- Plots `(non_null_count / len(df))` for each column.
- If `orientation` is omitted, the plot is vertical (`bottom`) for <=50 columns
  and horizontal (`left`) for more than 50 columns.
- `log=True` uses a logarithmic scale; this can make small completeness ratios
  easier to compare but requires careful axis interpretation.
- The function creates secondary axes for raw counts and percentages.

## `heatmap` notes

- Filters/sorts first, then removes variables with zero nullity variance: all
  full or all empty columns have no meaningful correlation and are omitted.
- Correlation is `df.isnull().corr()` after constant-column removal.
- The upper triangle is masked.
- Annotation text is post-processed: exact `1`/`-1` remain, near-perfect values
  become `<1` or `>-1`, and near-zero values become blank.
- There is no special large-dataset support; use dendrogram or pre-filtering for
  broad variable sets.

## `dendrogram` notes

- Filters first, then computes `x = np.transpose(df.isnull().astype(int).values)`
  and `scipy.cluster.hierarchy.linkage(x, method)`.
- Default `method` is `average`; other SciPy linkage methods can be passed.
- Default orientation is `bottom` for <=50 columns and `left` for >50 columns.
- Figure height grows for large horizontal displays.
- Interpreting a zero-distance leaf pair means their nullity patterns fully
  predict each other in the data supplied to the function.

## Unsupported in this snapshot

- No verified `inline` keyword exists in the plotting signatures. To customize
  or save plots, use the returned axes.
- No verified `geoplot` function is exported by `missingno` in this snapshot.
