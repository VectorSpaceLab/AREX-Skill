# Chartify Troubleshooting

## Install or Import Fails

**Symptoms**

- `ModuleNotFoundError: No module named 'chartify'`
- Dependency import errors for `bokeh`, `pandas`, `scipy`, `selenium`, `PIL`, `IPython`, or `yaml`.

**Recovery**

1. Use a supported Python version (`>=3.9,<4` for the source snapshot).
2. Install Chartify into the active environment: `pip install chartify`.
3. Run the root helper:

   ```bash
   python scripts/check_chartify_runtime.py --check-html-save
   ```

4. If dependency resolution is constrained by an old environment, create a clean environment and reinstall Chartify rather than mixing incompatible Bokeh/Pandas versions.

## Bokeh or IPython Display Confusion

**Symptoms**

- Notebook display works but automated checks cannot prove anything.
- `ch.show()` behavior differs between notebooks and non-notebook terminals.

**Likely causes**

- Chartify configures Bokeh notebook output when it detects a Jupyter kernel.
- Non-interactive agents usually run outside notebook display contexts.

**Recovery**

- Prefer object checks (`ch.data`, `ch.figure`, title/axis properties) and `ch.save(..., format='html')` for deterministic validation.
- Do not treat a missing visual notebook render as a core Chartify failure when the chart object and HTML output are valid.

## PNG/SVG Export Fails

**Symptoms**

- Selenium or browser-driver errors when saving or showing `format='png'` or `format='svg'`.
- `WebDriverException` from Bokeh/Selenium export.
- `TypeError: Object of type function is not JSON serializable` during SVG export on newer Bokeh/Selenium combinations.

**Likely causes**

- Chartify's README marks Chrome/Chromedriver as optional and needed for PNG output.
- The Python package can be installed while the system browser or driver is absent.

**Recovery**

1. Verify that HTML output works first:

   ```python
   ch.save("chart.html", format="html")
   ```

2. If SVG fails with a JSON-serialization error around Bokeh's SVG export script, treat it as a Chartify/Bokeh export compatibility issue rather than a data/plotting issue. Use HTML or PNG when acceptable, or pin/test a compatible Bokeh/Selenium export stack before requiring SVG.

3. Probe browser commands:

   ```bash
   python scripts/check_chartify_runtime.py --probe-browser
   ```

4. If PNG/SVG is required, install a compatible browser and driver for the host, then retry the export.
5. If the task does not require image export, document that PNG/SVG is unavailable and continue with HTML or chart-object validation.

## Plot Method Missing

**Symptoms**

- `AttributeError: Plot 'bar' not available for the given Chart...`
- A method shown in examples is absent from `dir(ch.plot)`.

**Recovery**

Use [`basic-charting/references/api-reference.md`](../sub-skills/basic-charting/references/api-reference.md#axis-type-to-plot-method-routing) to choose the correct `x_axis_type`/`y_axis_type`. For example, `bar` requires a categorical axis, `heatmap` requires both axes categorical, and `hexbin` requires both axes density.

## DataFrame Shape Problems

**Symptoms**

- Numeric-axis errors when a column is object dtype.
- Datetime values plotted on a numeric axis.
- Categorical charts show duplicate or unexpected factors.

**Recovery**

- Use named `DataFrame` columns for every plotted dimension; do not pass Series or index-only groupby outputs.
- Use `reset_index()` after pandas groupby operations.
- Use `pd.melt(...)` for pivoted tables.
- Use `x_axis_type='datetime'` for datetime x columns.
- For categorical charts, aggregate duplicate category combinations before plotting and set factor order explicitly if needed.

See [`basic-charting/references/data-formats.md`](../sub-skills/basic-charting/references/data-formats.md).

## Config or Palette Defaults Do Not Load

**Symptoms**

- `CHARTIFY_CONFIG_DIR` appears ignored.
- Custom palette/config files do not affect new charts.
- Palette lookup raises `KeyError`.

**Recovery**

- Set `CHARTIFY_CONFIG_DIR` before importing Chartify and include a trailing path separator.
- Use trusted local YAML only; some Chartify config files use unsafe YAML loading for Python objects.
- Run [`styling-annotations/scripts/check_chartify_style_config.py`](../sub-skills/styling-annotations/scripts/check_chartify_style_config.py) with `--print-options` and `--check-palette NAME`.
- Read [`styling-annotations/references/configuration.md`](../sub-skills/styling-annotations/references/configuration.md) for file names and safe writing patterns.

## When to Stop

Stop and ask for user/system action only when:

- The requested PNG/SVG output is mandatory but no compatible browser driver can be installed or used.
- The requested code must load untrusted Chartify YAML config; rewrite the workflow to validate preferences and write trusted config instead.
- The requested chart depends on non-public Bokeh internals beyond Chartify's exposed API; decide whether to use Bokeh directly rather than forcing Chartify.
