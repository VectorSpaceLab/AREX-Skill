# Function Interface Troubleshooting

## Could Not Interpret Variable

Likely causes: `data=` missing, typo in a column name, or a wide-form/vector call mixed with long-form variable strings.

Recovery: inspect `df.columns`, pass `data=df`, or switch to direct vectors (`x=array, y=array`). Use `../data-utilities/scripts/validate_plot_data.py` for CSV preflight.

## Figure-level Function Ignores `ax`

`relplot`, `displot`, `catplot`, and `lmplot` own their figure. Replace them with axes-level counterparts or customize the returned grid object.

## Optional Dependency Errors

- Install `seaborn[stats]` for SciPy/statsmodels-backed functionality.
- Use `heatmap` instead of `clustermap` when SciPy is unavailable.
- Use ordinary linear `regplot` instead of `lowess`, `logistic`, or `robust` when statsmodels is unavailable.

## KDE Singular or Weird Density

KDE needs variation. Constant/tiny groups can warn or produce misleading curves. Use `histplot`, reduce semantic grouping, increase data, or set `warn_singular=False` only when the limitation is understood.

## Numeric Categorical Alignment

Categorical plots may map levels to positions 0, 1, 2. Use `native_scale=True` when supported or explicitly map categories before overlaying line/regression plots.

## Heatmap Mask Shape

A heatmap mask must have the same shape as the plotted data. If using a pandas DataFrame mask, align both index and columns to the data.
