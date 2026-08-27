---
name: basic-charting
description: "Build core Chartify charts from tidy pandas DataFrames, choose
  axis types and plot methods, inspect plotted data, and save or show chart
  outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Basic Charting

Use this sub-skill when a task asks for core Chartify chart construction from pandas DataFrames: line, scatter, text, area, bar, stacked bar, boxplot, interval, lollipop, parallel, heatmap, density, radar, or second-y-axis charts. This sub-skill owns Chart and RadarChart creation, axis-type selection, plot-method routing, data-shape preparation, labels/legends enough for basic chart workflows, `Chart.data` inspection, and `show`/`save` output calls.

Route palette creation, YAML options/style configuration, callout-heavy annotation, and advanced axis formatting to sibling `styling-annotations`. Keep maintainer docs, package release, and documentation-build workflows out of this sub-skill.

## Read/Run These Files

- Read [references/api-reference.md](references/api-reference.md) when choosing `Chart(...)` or `RadarChart(...)` arguments, selecting a plot method, or checking method signatures and return objects.
- Read [references/data-formats.md](references/data-formats.md) when converting pandas results into Chartify's tidy input format or debugging grouped/pivoted data.
- Read [references/workflows.md](references/workflows.md) when you need compact, self-contained chart construction patterns for common chart families, save/show, data inspection, radar charts, or second-y-axis charts.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a plot method is unavailable, dtypes do not match axis types, grouped categorical data orders incorrectly, second-y-axis plotting fails, or PNG/SVG export needs a browser driver.
- Run [scripts/chartify_smoke_examples.py](scripts/chartify_smoke_examples.py) to exercise safe tiny examples without notebook display or network access; use `--list`, `--case`, and optional `--save-html DIR`.

## Fast Routing Rules

1. Start with `import chartify` and a pandas `DataFrame` with named columns.
2. Choose axis types before choosing the plot method:
   - numeric/datetime x with numeric y: `Chart(x_axis_type="linear"|"log"|"datetime", y_axis_type="linear"|"log")` and `line`, `scatter`, `text`, or `area`.
   - categorical plus numeric: make the categorical axis explicit with `x_axis_type="categorical"` for vertical charts or `y_axis_type="categorical"` for horizontal charts, then use mixed-type methods such as `bar`, `bar_stacked`, `boxplot`, `interval`, `lollipop`, `parallel`, `scatter`, or `text`.
   - categorical/categorical heatmap: set both axis types to `"categorical"`.
   - density charts: set one or both axes to `"density"` for `histogram`, `kde`, or `hexbin`.
   - radar: use `RadarChart(...)`, not `Chart(...)`.
3. Convert groupby/pivot outputs to tidy DataFrames before plotting: use `.reset_index()` after `groupby` and `pd.melt` or `stack().reset_index(...)` for wide tables.
4. Add basic labels with `set_title`, `set_subtitle`, `set_source_label`, and legend placement with `set_legend_location` after plotting grouped/color data.
5. Inspect `ch.data` for a list of plotted Bokeh `ColumnDataSource.data` dictionaries before saving or returning a chart object.
