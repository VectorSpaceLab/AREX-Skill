# Visualization Workflows

## When to read

Read this when a task asks which `missingno` plot to use, how to make a plot
from a pandas DataFrame, how to save it in scripts, or how to interpret common
missingness patterns.

## Minimal plotting pattern

```python
import matplotlib.pyplot as plt
import missingno as msno

ax = msno.matrix(df, sparkline=False)  # df is a pandas.DataFrame
ax.figure.savefig("missingness-matrix.png", bbox_inches="tight")
plt.close(ax.figure)
```

For CI or servers, set `MPLBACKEND=Agg` before Python starts, or configure the
Agg backend before importing `pyplot`.

## Matrix: dense row/column completeness scan

Use `matrix` when you need to see whether missing values occur in runs, blocks,
or row-wise patterns.

```python
ax = msno.matrix(df, filter="bottom", n=30, sparkline=True, labels=True)
```

Decision notes:

- Use `sparkline=False` when reusing an existing axis or when the sparkline is
  visually distracting.
- Use `labels=False` or pre-filter columns when there are more than 50 columns.
- Use `color=(r, g, b)` with floats in `[0, 1]` to change present-value color.
- For time-series display, use `freq` only when the index is a pandas
  `PeriodIndex` or `DatetimeIndex`.

## Bar: per-column completeness comparison

Use `bar` when the task is to rank or report column completeness ratios/counts.

```python
ax = msno.bar(df, filter="top", p=0.8, labels=True, log=False)
```

Decision notes:

- `log=True` can help when ratios vary across orders of magnitude.
- Omitted `orientation` defaults to vertical for <=50 columns and horizontal for
  wider frames.
- The bars show non-null counts divided by row count; secondary axes expose raw
  counts.

## Heatmap: pairwise nullity correlation

Use `heatmap` when the task asks whether the presence/absence of one variable is
related to another.

```python
ax = msno.heatmap(df, filter="bottom", n=25, cmap="RdBu", labels=True)
```

Interpretation:

- `1` means two variables are present/missing together in the supplied data.
- `-1` means one is present exactly when the other is missing.
- Values near `0` mean little pairwise relationship and may be blanked in the
  plot labels.
- Labels `<1` and `>-1` are near-perfect but not exact relationships; inspect
  mismatching rows before imputing or dropping data.
- All-full and all-empty columns are removed before correlation because their
  nullity variance is zero.

## Dendrogram: grouped missingness structure

Use `dendrogram` when pairwise heatmap relationships are not enough or when many
columns need grouped pattern interpretation.

```python
ax = msno.dendrogram(df, filter="bottom", n=50, method="average")
```

Interpretation:

- Leaves that join at distance zero have identical or perfectly predictive
  nullity patterns in the supplied data.
- Near-zero splits indicate strong but imperfect relationships; inspect the
  rows responsible for mismatches.
- The default orientation changes from `bottom` to `left` when there are more
  than 50 columns.
- Pass a SciPy linkage `method` such as `single`, `complete`, or `average` when
  a specific clustering behavior is desired.

## Filtering before plotting

The plotting APIs accept `filter`, `n`, `p`, and some accept `sort`. For exact
semantics, read the nullity utilities sub-skill. Common patterns:

```python
# Ten least-complete columns.
msno.matrix(df, filter="bottom", n=10)

# Columns at least 90% complete, capped at five columns.
msno.bar(df, filter="top", p=0.9, n=5)

# Sort rows in the matrix by row completeness.
msno.matrix(df, sort="ascending")
```

## Saving and adapting returned axes

Every plot returns a matplotlib `Axes` object:

```python
ax = msno.heatmap(df, labels=False)
ax.set_title("Nullity correlation")
ax.figure.savefig("nullity-heatmap.png", dpi=150, bbox_inches="tight")
```

Do not pass an unverified `inline=False` keyword. In this snapshot, returning an
axis is already the public customization path.

## Use the smoke helper

To validate an environment without network data:

```bash
MPLBACKEND=Agg python scripts/missingno_smoke_check.py --plot all --output-dir /tmp/missingno-smoke
```

Run that command from the generated skill root. It creates deterministic
synthetic missingness and checks all four plot functions.
