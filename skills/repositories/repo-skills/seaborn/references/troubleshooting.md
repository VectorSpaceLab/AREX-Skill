# seaborn Troubleshooting

## Import or Install Fails

Symptoms:

- `ModuleNotFoundError: No module named 'seaborn'`.
- A long traceback while importing NumPy, pandas, matplotlib, SciPy, or statsmodels.
- Seaborn installed in one terminal but unavailable in a notebook.

Recovery:

1. Verify the active interpreter: `python -c "import sys; print(sys.executable)"`.
2. Install with the same interpreter: `python -m pip install seaborn` or `python -m pip install 'seaborn[stats]'`.
3. In notebooks, prefer `%pip install seaborn` so installation targets the kernel.
4. If a compiled dependency fails with DLL/shared-library errors, identify which dependency is failing and repair that package/environment. Seaborn itself is pure Python.
5. Run `python scripts/check_seaborn_environment.py --render-smoke` after installation.

## Plots Do Not Display

Symptoms:

- Code runs but no figure appears.
- A script exits without showing a window.
- Notebook prints `<Axes: ...>` or `<seaborn.axisgrid.FacetGrid ...>` above a plot.

Recovery:

1. In scripts, call `matplotlib.pyplot.show()` for interactive display or `figure.savefig(...)` for files.
2. In headless/CI contexts, set `matplotlib.use("Agg")` before importing `pyplot` and save figures to disk.
3. In notebooks, assign the returned object (`ax = ...`, `g = ...`) or end the plotting line with `;` to suppress object repr output.
4. If plots look fuzzy inline, adjust matplotlib DPI or use retina/SVG notebook output.

## Optional Statistical Feature Fails

Symptoms:

- `clustermap requires scipy to be available`.
- `Cumulative KDE evaluation requires scipy`.
- Regression options such as `lowess=True`, `logistic=True`, or `robust=True` require statsmodels.

Recovery:

1. Install the optional statistical extra: `python -m pip install 'seaborn[stats]'`.
2. For `clustermap`, check SciPy import before debugging seaborn code.
3. For lowess/logistic/robust regression, check statsmodels import and then reduce data size if the model is slow or unstable.
4. If optional dependencies are unavailable, choose a supported base plot (`regplot` with ordinary linear fit, `heatmap` without clustering, or `histplot`/non-cumulative `kdeplot`).

## Example Dataset or Network Fails

Symptoms:

- `sns.load_dataset("...")` hangs or raises network errors.
- `ValueError: '<name>' is not one of the example datasets.`
- `TypeError: This function accepts only strings` after passing a DataFrame to `load_dataset`.

Recovery:

1. Do not require `load_dataset` for production/reusable examples; generate synthetic data or read a local CSV.
2. If using seaborn examples, call `sns.get_dataset_names()` only when network access is acceptable.
3. Set `SEABORN_DATA` or pass `data_home=` to control cache location.
4. If the user already has a DataFrame, pass it directly to a plotting function with `data=df`.

## Figure-level Function Sent to Existing Axes

Symptoms:

- User writes `fig, ax = plt.subplots(); sns.catplot(..., ax=ax)` and gets an extra figure or blank axes.
- Warning that `ax` is ignored.

Recovery:

1. Use an axes-level function (`stripplot`, `boxplot`, `histplot`, `scatterplot`, `regplot`, `heatmap`, etc.) when drawing into existing axes.
2. Use figure-level functions (`catplot`, `relplot`, `displot`, `lmplot`) when seaborn should own facets and figure size.
3. After a figure-level call, customize through the returned grid object: `g.figure`, `g.axes`, `g.set(...)`, and `sns.move_legend(g, ...)`.
4. Route layout questions to `sub-skills/figure-grids/`.

## Data Shape or Semantic Errors

Symptoms:

- `Could not interpret value ... for x/y/hue`.
- Plot output ignores a grouping variable.
- Numeric categorical labels do not align with overlaid line plots.
- Heatmap mask shape mismatch.

Recovery:

1. Confirm all named variables exist in `data` and that `data=` was passed.
2. Reshape to long-form when multiple semantic mappings are needed.
3. For wide-form quick views, omit `x`/`y` variable assignments and pass the whole table.
4. Use `native_scale=True` on categorical functions when numeric/datetime axis spacing must be preserved.
5. Validate heatmap mask shape against the plotted 2D data.
6. Run `python sub-skills/data-utilities/scripts/validate_plot_data.py --csv data.csv --x ... --y ...` for a reusable preflight.

## Palette or Style Problems

Symptoms:

- `ValueError` for invalid palette names.
- Qualitative palette requested as a continuous colormap.
- Dark background reduces contrast.
- Theme changes leak into later plots.

Recovery:

1. Use `sns.color_palette(name)` to validate names before plotting.
2. Do not request `as_cmap=True` for qualitative ColorBrewer palettes.
3. For dark backgrounds, prefer brighter/muted/pastel palettes or set the palette after applying a matplotlib dark style.
4. Use context managers (`with sns.axes_style(...):`, `with sns.plotting_context(...):`, `with sns.color_palette(...):`) for temporary changes.
5. Run `sns.reset_defaults()` or `sns.set_theme()` to restore known defaults.
