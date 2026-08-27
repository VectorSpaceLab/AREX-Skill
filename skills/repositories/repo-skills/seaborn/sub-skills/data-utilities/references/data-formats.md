# seaborn Data Formats

## Long-form

Long-form data is best when mapping variables to roles:

```python
sns.scatterplot(data=df, x="x", y="y", hue="group", style="condition")
```

Each role string must be a column name. This format supports most seaborn semantics and faceting.

## Wide-form

Wide-form data is useful for quick plotting of many columns:

```python
sns.lineplot(data=wide_df)
```

When using wide-form data, omit `x`, `y`, and semantic mappings unless the function documents a specific behavior.

## Vector Inputs

Use direct arrays or Series for small scripts:

```python
sns.histplot(x=values)
sns.lineplot(x=time, y=signal)
```

If a user wants `hue`, `row`, or `col`, a DataFrame is usually clearer.

## Matrix Inputs

`heatmap` and `clustermap` expect 2D rectangular data. A pandas DataFrame preserves row/column labels. Masks and annotations must match the plotted shape.

## Categorical Ordering

Use `order=`, `hue_order=`, pandas categorical dtype, or explicit sorting when display order matters. Use `native_scale=True` when numeric/datetime categorical positions should keep native spacing.
