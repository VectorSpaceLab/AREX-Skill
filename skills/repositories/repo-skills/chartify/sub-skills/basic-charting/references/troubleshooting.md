# Basic Charting Troubleshooting

Use this file for core Chart/RadarChart construction, plot routing, tidy DataFrame shape, data inspection, second-y-axis, and output rendering failures. Palette design, YAML options/style config, callout-heavy annotation, and advanced axis formatting route to `styling-annotations`.

## Failure Matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `AttributeError: Plot 'bar' not available...` or another missing plot method | The selected `Chart(x_axis_type=..., y_axis_type=...)` creates a different plot namespace. | Recreate the chart with the axis types required by the method. Example: `bar` needs one categorical axis and one numeric/log axis; `heatmap` needs both axes categorical; `line` needs numeric/datetime x and numeric y. |
| `ValueError: Set chartify.Chart(x_axis_type='datetime') when plotting datetime data.` | A datetime x column was passed to a chart whose x-axis is numeric/log instead of datetime. | Use `chartify.Chart(x_axis_type="datetime", y_axis_type="linear")`, cast with `pd.to_datetime`, and sort by the date column. |
| `Attempting to plot <column> on a numeric axis...` | Object/string data is being plotted on a numeric x-axis, or the wrong axis type was selected. | If the data is numeric, cast with `pd.to_numeric(..., errors="raise")`; if it is categorical, use a categorical axis and a mixed-type method. |
| `KeyError` for a plot column | The column name is absent because a groupby key is still in the index, the data is a Series, or the wide table was not melted. | Convert to a tidy DataFrame: `.groupby(..., as_index=False)` or `.reset_index()`, and `pd.melt(...)` for wide tables. |
| Error about each categorical grouping having at most one observation | Mixed categorical methods that pivot internally received duplicate rows for the same category/stack combination. | Aggregate first with `groupby(categorical_columns + stack/color columns, as_index=False).agg(...)`. `boxplot` and categorical `scatter` are the main exceptions that can use repeated observations. |
| `Color order must include all unique factors...` | `color_order` omits at least one value present in `color_column`. | Build `color_order` from the data or include all current values: `color_order=list(df[color_column].unique())` in desired order. |
| Stacked bar/text order error | `stack_order` omits a `stack_column` value. | Include every stack factor in `stack_order`, in the desired order. |
| Categorical axis order is surprising | Default ordering differs by method: bars often sort by values, categorical scatter often sorts by count, boxplot often sorts by labels. | Pass `categorical_order_by="labels"`, `"values"`, or an explicit list, and set `categorical_order_ascending` deliberately. |
| `ValueError` when constructing `Chart(..., second_y_axis=True)` | Second y-axis was requested with a categorical or density y-axis. | Use `y_axis_type="linear"` or `"log"`, then plot second-axis data with `ch.second_axis.plot.*`. |
| `AttributeError: 'Chart' object has no attribute 'second_axis'` | The chart was not constructed with `second_y_axis=True`. | Recreate it with `chartify.Chart(..., second_y_axis=True)`. |
| PNG/SVG save/show fails with Selenium, browser-driver, or SVG serialization errors | HTML works through Bokeh directly, but PNG/SVG export uses Selenium and Bokeh export internals that can vary by dependency version. | Use `format="html"` for smoke checks. If PNG/SVG is required, install a compatible browser/driver and pin/test a compatible Bokeh/Selenium export stack; treat errors such as `TypeError: Object of type function is not JSON serializable` during SVG export as export-stack compatibility, not a chart-data failure. |
| Empty or unexpected `ch.data` | The DataFrame slice is empty, a color factor has no rows, or a plot call used a different source than expected. | Inspect input row counts before plotting and inspect `ch.data` after plotting; verify `color_column`, `color_order`, and filters. |
| Hexbin data-source row order differs across dependency versions | Bokeh/Chartify hex tiling may produce the same bins in a different row order than an older golden test expected. | Validate the presence of `q`, `r`, and `c` columns and aggregate/bin counts instead of relying on raw row order unless the task explicitly requires that version-specific ordering. |

## Plot Method Not Available

Chartify chooses a plot class at chart construction time. Changing the data after construction does not add methods. Recreate the chart with compatible axis types.

```python
# Wrong: default numeric/numeric chart has no bar method.
ch = chartify.Chart(blank_labels=True)
# ch.plot.bar(...)  # AttributeError

# Correct vertical bar chart.
ch = chartify.Chart(blank_labels=True, x_axis_type="categorical", y_axis_type="linear")
ch.plot.bar(df, categorical_columns="fruit", numeric_column="quantity")
```

Quick method routing:

- `line`, `scatter`, `text`, `area`: numeric/log/datetime x and numeric/log y.
- `bar`, `bar_stacked`, `boxplot`, `interval`, `lollipop`, `parallel`, categorical `scatter`/`text`: one categorical axis plus one numeric/log axis.
- `heatmap`: categorical x and categorical y.
- `histogram`, `kde`: one density axis.
- `hexbin`: density x and density y.
- Radar methods: `RadarChart`, not `Chart`.

## Datetime and Object Dtype Problems

Use a datetime x-axis for dates:

```python
df["date"] = pd.to_datetime(df["date"])
ch = chartify.Chart(blank_labels=True, x_axis_type="datetime")
ch.plot.line(df.sort_values("date"), "date", "value")
```

Use numeric dtype for numeric axes:

```python
df["value"] = pd.to_numeric(df["value"], errors="raise")
ch = chartify.Chart(blank_labels=True)
ch.plot.scatter(df, "x", "value")
```

If the column is categorical text, do not cast it to numeric; use a categorical axis and a mixed-type method instead.

## Grouped Categorical Data and Ordering

For grouped bars, keep one row per displayed combination:

```python
clean = raw.groupby(["fruit", "country"], as_index=False)["quantity"].sum()

ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
ch.plot.bar(
    clean,
    categorical_columns=["fruit", "country"],
    numeric_column="quantity",
    color_column="country",
    categorical_order_by="labels",
    categorical_order_ascending=True,
)
```

If the source table is pivoted, melt it first:

```python
long = pd.melt(wide, id_vars="fruit", var_name="country", value_name="quantity")
```

If an explicit category order is needed, pass a list:

```python
ch.plot.bar(clean, "fruit", "quantity", categorical_order_by=["Banana", "Apple", "Orange"])
```

## Color and Stack Factor Coverage

`color_order` and `stack_order` are validation lists, not filters. They must cover all factors present in the DataFrame passed to that plot call.

```python
factors = ["baseline", "candidate"]
assert set(df["model"].unique()).issubset(factors)
ch.plot.line(df, "x", "y", color_column="model", color_order=factors)
```

For stacked bars:

```python
stack_order = ["CA", "US"]
assert set(df["country"].unique()).issubset(stack_order)
ch.plot.bar_stacked(df, "fruit", "quantity", "country", stack_order=stack_order)
```

If a plot is made after another plot and colors should align, reset the palette order between calls:

```python
ch.plot.kde(df, "score", color_column="cohort")
ch.style.color_palette.reset_palette_order()
ch.plot.histogram(df, "score", color_column="cohort", method="density")
```

## Second Y-Axis Limitations

Second-axis charts are numeric/log y-axis charts only.

```python
ch = chartify.Chart(blank_labels=True, x_axis_type="datetime", y_axis_type="linear", second_y_axis=True)
ch.plot.line(df, "date", "orders")
ch.second_axis.plot.line(df, "date", "revenue")
ch.second_axis.axes.set_yaxis_label("Revenue")
```

Avoid:

```python
chartify.Chart(y_axis_type="categorical", second_y_axis=True)  # invalid
chartify.Chart(y_axis_type="density", second_y_axis=True)      # invalid
```

The second axis has its own `axes` and `plot` namespaces. Label or range the first axis with `ch.axes.*` and the second axis with `ch.second_axis.axes.*`.

## Save/Show and Browser Driver Caveats

HTML output is the safest default:

```python
ch.save("chart.html", format="html")
# or interactively:
ch.show("html")
```

PNG/SVG output uses a headless browser through Selenium:

```python
ch.save("chart.png", format="png")
ch.save("chart.svg", format="svg")
```

If PNG/SVG fails, the Chartify chart may be fine. Confirm with HTML output first. Install a compatible browser and driver only when image export is required by the task. If SVG fails with a JSON-serialization error involving Bokeh's SVG export script, use HTML/PNG when acceptable or test a compatible Bokeh/Selenium export stack before promising SVG output.

## Debug with `ch.data`

After plotting, inspect the Bokeh data sources Chartify created:

```python
for i, source in enumerate(ch.data):
    print(i, sorted(source.keys()))
```

Expected examples:

- numeric line grouped by `segment`: separate sources containing `date`, value column, and `segment` for each factor.
- categorical bar: source containing `factors` and the numeric column.
- heatmap: source containing x category, y category, and color/text columns.
- hexbin: source containing hex coordinates such as `q`/`r` and counts such as `c`; row order can vary across Bokeh/Chartify dependency versions, so validate bins by content when possible.
- radar: transformed sources include internal coordinate columns plus the radius column.

If `ch.data` is empty or a source lacks expected columns, verify the DataFrame slice, plot arguments, and selected axis types before saving.
