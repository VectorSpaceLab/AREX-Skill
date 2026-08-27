# EDA visualization troubleshooting

## No plots or fewer plots than expected

- Check whether `depVar` exists in the DataFrame.
- Check whether columns were classified as ID or low-information columns and removed.
- Tiny examples with values such as `[1, 2, 1, 2]` can be treated as boolean or categorical, not continuous.
- `max_cols_analyzed` can reduce the variable set when many columns are present.

## File loading issues

- For DataFrames, use `filename=""` and `dfte=df`.
- For CSV files, set `sep` correctly.
- For Excel files, ensure `xlrd` or the appropriate pandas Excel engine is installed.
- Duplicate column names are removed by AutoViz after load.

## Saving issues

- Use `verbose=2` to save charts.
- Provide a writable `save_plot_dir` to avoid confusion about where `AutoViz_Plots` was created.
- AutoViz adds a target-named subdirectory when `depVar` is nonempty.

## Static plotting issues

- Use `chart_format='png'` for safe headless checks.
- Use `chart_format='svg'` for notebook-friendly vector output.
- If matplotlib/seaborn fails, verify the package environment with the root install reference and run the smoke script.

## Interactive plotting issues

- `bokeh`, `server`, and `html` depend on HoloViews/Bokeh/Panel. Missing imports mean the interactive stack is incomplete.
- Use `html` for saved interactive files when a browser or live server is unavailable.
- Avoid `server` unless the user explicitly wants a live dashboard.

## Data-quality failures during plotting

AutoViz runs `data_cleaning_suggestions` before plotting. If the run fails inside `pandas_dq`, route to the data-quality sub-skill and fix pandas/IPython compatibility before debugging plots.
