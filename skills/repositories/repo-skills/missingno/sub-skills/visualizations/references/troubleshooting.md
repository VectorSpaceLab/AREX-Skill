# Visualization Troubleshooting

## Headless backend errors

Symptoms:

- A plot command hangs in CI or an agent environment.
- Errors mention a missing display, GUI backend, or Tk/Qt.

Recovery:

1. Set a non-interactive backend before Python starts:
   ```bash
   MPLBACKEND=Agg python your_script.py
   ```
2. Or configure Agg before importing `matplotlib.pyplot`:
   ```python
   import matplotlib
   matplotlib.use("Agg", force=True)
   ```
3. Save and close figures explicitly:
   ```python
   ax = msno.matrix(df, sparkline=False)
   ax.figure.savefig("matrix.png", bbox_inches="tight")
   plt.close(ax.figure)
   ```

## Matrix labels overlap or disappear

Symptoms:

- Column labels overlap badly.
- Labels are missing on a matrix with many columns.

Likely causes:

- `matrix` shows labels by default only for up to 50 columns.
- Large variable sets are hard to read in a dense matrix.

Recovery:

- Filter to the most relevant columns first, for example
  `filter="bottom", n=20` for least-complete columns.
- Pass `labels=False` intentionally when labels would be unreadable.
- Increase `figsize`, reduce `fontsize`, or change `label_rotation`.
- Use `bar` for simple completeness ranking or `dendrogram` for grouped
  structure across many columns.

## `matrix(freq=...)` raises `KeyError`

Symptoms:

- `KeyError: 'Dataframe index must be PeriodIndex or DatetimeIndex.'`
- `KeyError: 'Could not divide time index into desired frequency.'`

Likely causes:

- The DataFrame index is not a pandas `PeriodIndex` or `DatetimeIndex`.
- The requested frequency creates tick values that are not present in the index.

Recovery:

```python
df = df.copy()
df.index = pandas.to_datetime(df.index)
ax = msno.matrix(df, freq="MS")  # choose a frequency compatible with the index range
```

If exact tick placement matters, build a regular `DatetimeIndex`/`PeriodIndex`
first and verify it spans the requested frequency.

## Heatmap omits columns

Symptom: a full or empty column exists in the DataFrame but is absent from the
heatmap.

Reason: `heatmap` removes columns with zero variance in `df.isnull()` before
computing correlation. A column that is always full or always missing has no
meaningful nullity correlation.

Recovery:

- Explain the omission as expected behavior, not data loss.
- Use `bar` to show all per-column completeness counts.
- Use `matrix` if the user needs to display constant columns alongside partial
  columns.

## Near-perfect heatmap labels are confusing

Symptoms:

- Labels show `<1` or `>-1`.
- Some cells have no label.

Interpretation:

- `<1` means a strong positive correlation that is close to but not exactly 1.
- `>-1` means a strong negative correlation that is close to but not exactly -1.
- Near-zero correlations may be blanked for readability.

Recovery: inspect mismatching rows before deciding that two columns should be
imputed, joined, or dropped together.

## Existing axis plus matrix sparkline warning

Symptom: a warning says plotting a sparkline on an existing axis is not
currently supported.

Recovery: pass `sparkline=False` when using `ax=`:

```python
fig, ax = plt.subplots(figsize=(8, 4))
msno.matrix(df, ax=ax, sparkline=False)
```

## Unsupported `inline` or `geoplot`

- If `inline=False` raises a `TypeError`, remove it. Use the returned axes for
  customization and saving.
- If `msno.geoplot` is missing, do not use it for this snapshot. The verified
  exports are `matrix`, `bar`, `heatmap`, `dendrogram`, `nullity_filter`, and
  `nullity_sort`.
