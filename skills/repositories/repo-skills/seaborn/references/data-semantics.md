# Shared Data Semantics

## Purpose

Read this when a seaborn task is blocked by input shape, variable assignment, semantic mapping, or example dataset confusion. Detailed validation help lives in `sub-skills/data-utilities/`.

## Long-form Data

Long-form (tidy) data is the most flexible seaborn contract: each variable is a column, each observation is a row, and plot roles are named with strings.

```python
sns.scatterplot(data=df, x="bill_length", y="bill_depth", hue="species")
```

If `x`, `y`, `hue`, `size`, `style`, `row`, `col`, or similar variables are strings, pass the table through `data=`. Without `data=`, seaborn cannot resolve column names.

## Wide-form Data

Most functions also accept wide-form data when `data=` is provided and explicit `x`/`y` variable names are omitted:

```python
sns.lineplot(data=wide_df)
```

Wide-form mode gives a quick view of columns but is less expressive: grouping semantics are inferred from structure and vary by plot family. Reshape to long-form when the user needs multiple semantic mappings or precise labels.

## Vector and Mapping Inputs

For small scripts, arrays/lists/Series can be passed directly:

```python
sns.histplot(x=np.asarray(values))
sns.lineplot(x=time, y=signal)
sns.scatterplot(data={"x": xs, "y": ys, "group": labels}, x="x", y="y", hue="group")
```

A few older figure-level functions are more DataFrame-oriented; if a function rejects vector data, convert to a pandas DataFrame first.

## Semantic Mappings

- `hue` maps color to levels or numeric values.
- `size` maps marker/line size.
- `style` maps markers/dashes.
- `row`/`col` facet by categories in figure-level functions.
- `units` draws repeated-measures lines without adding legend entries.
- `weights` is supported by selected estimators/plot families.

Numeric and categorical semantics are treated differently. Numeric `hue` often gets a continuous colormap and brief tick-like legend; categorical `hue` gets discrete palette entries.

## Categorical Axis and Native Scale

Categorical functions historically map category levels to integer positions even if labels are numeric. This can surprise users who overlay a line/regression plot on top of a categorical plot. Prefer one of these fixes:

1. Use `native_scale=True` when the categorical function supports preserving numeric/datetime positions.
2. Use a categorical plot such as `pointplot` for both summary and line-like display.
3. Explicitly map categories to integer positions before overlaying a non-categorical matplotlib/seaborn function.

## Example Dataset Utilities

`sns.load_dataset(name)` downloads example CSV data from the seaborn-data repository and can cache it locally. It is useful for examples and bug reports, not for loading a user's existing DataFrame.

- Use `sns.get_dataset_names()` to list online example datasets; this requires network.
- Use `sns.get_data_home()` to find/create the example-data cache directory.
- The `SEABORN_DATA` environment variable can redirect the cache.
- Passing a pandas DataFrame to `load_dataset` is an error; plot the DataFrame directly.

## Validation Before Plotting

Before writing a plot, check:

- All named variables exist in `data`.
- Numeric plot axes are numeric or intentionally categorical.
- Hue/order/palette dictionaries contain all expected levels.
- Heatmap data and masks have the same 2D shape.
- The caller wants an axes-level function when they already created axes.
- Network-backed example datasets are not required for reproducible scripts.

Use `sub-skills/data-utilities/scripts/validate_plot_data.py` for a reusable local preflight.
