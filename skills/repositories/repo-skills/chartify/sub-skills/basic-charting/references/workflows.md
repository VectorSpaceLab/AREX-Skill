# Basic Charting Workflows

These workflows are compact patterns for constructing Chartify charts from small or prepared pandas DataFrames. They avoid notebook-only display calls until the final optional `show`/`save` step.

## 1. Numeric or Datetime Line/Scatter/Text/Area

Use numeric/datetime plot methods when both axes are numeric, or when the x-axis is datetime and y-axis is numeric.

```python
import pandas as pd
import chartify

raw = pd.DataFrame({
    "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-01-01", "2024-02-01"]),
    "segment": ["A", "A", "B", "B"],
    "revenue": [10, 14, 7, 12],
})

# Groupby results must be reset back to named columns.
monthly = (
    raw.groupby(["date", "segment"], as_index=False)["revenue"]
    .sum()
    .sort_values("date")
)

ch = chartify.Chart(blank_labels=True, x_axis_type="datetime", y_axis_type="linear")
ch.plot.line(monthly, x_column="date", y_column="revenue", color_column="segment")
ch.set_title("Monthly revenue")
ch.set_subtitle("Line data sorted by date")
ch.set_legend_location("outside_bottom")

# Inspect before saving or returning.
assert ch.data
ch.save("monthly_revenue.html", format="html")
```

Variants:

- `ch.plot.scatter(df, "x", "y", size_column="size", color_column="group")` for point charts.
- `ch.plot.text(df, "x", "y", "label", color_column="group")` to place labels at numeric/datetime points.
- `ch.plot.area(df, "x", "upper")` for area from zero; pass `second_y_column="lower"` for a band; pass `color_column` and `stacked=True` for stacked areas.

## 2. Categorical Bar from a Pivoted Sales Table

Chartify expects tidy named columns. If data starts wide or pivoted, melt it first.

```python
import pandas as pd
import chartify

pivoted_sales = pd.DataFrame({
    "fruit": ["Apple", "Banana"],
    "US": [12, 9],
    "CA": [7, 4],
})

sales = pd.melt(
    pivoted_sales,
    id_vars="fruit",
    var_name="country",
    value_name="quantity",
)

ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
ch.plot.bar(
    data_frame=sales,
    categorical_columns=["fruit", "country"],
    numeric_column="quantity",
    color_column="country",
    categorical_order_by="labels",
    categorical_order_ascending=True,
)
ch.set_title("Sales by fruit and country")
ch.set_legend_location("outside_bottom")
```

For a stacked version, keep one row per `fruit`/`country` combination and use:

```python
ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
ch.plot.bar_stacked(
    data_frame=sales,
    categorical_columns="fruit",
    numeric_column="quantity",
    stack_column="country",
    stack_order=["CA", "US"],
)
```

Use `y_axis_type="categorical"` instead of `x_axis_type="categorical"` for horizontal bars.

## 3. Heatmap from Two Categorical Dimensions

```python
import pandas as pd
import chartify

heat = pd.DataFrame({
    "fruit": ["Apple", "Apple", "Banana", "Banana"],
    "country": ["US", "CA", "US", "CA"],
    "avg_price": [1.2, 1.0, 0.6, 0.7],
})

ch = chartify.Chart(blank_labels=True, x_axis_type="categorical", y_axis_type="categorical")
ch.plot.heatmap(
    data_frame=heat,
    x_column="fruit",
    y_column="country",
    color_column="avg_price",
    text_column="avg_price",
    text_color="white",
)
ch.set_title("Average price heatmap")
ch.axes.set_xaxis_label("Fruit")
ch.axes.set_yaxis_label("Country")
```

Heatmap's `color_column` should be numeric; if there are duplicate cells, aggregate first with `groupby([...], as_index=False)`.

## 4. Histogram, KDE, and Hexbin Density Charts

```python
import pandas as pd
import chartify

values = pd.DataFrame({
    "score": [1.2, 1.4, 1.8, 2.1, 2.4, 2.9, 3.1, 3.2],
    "cohort": ["A", "A", "A", "B", "B", "B", "B", "A"],
})

# Vertical density/count axis.
ch = chartify.Chart(blank_labels=True, y_axis_type="density")
ch.plot.histogram(values, values_column="score", color_column="cohort", bins=3, method="count")
ch.set_title("Score distribution")

# Overlay-compatible density variant.
ch2 = chartify.Chart(blank_labels=True, y_axis_type="density")
ch2.plot.kde(values, values_column="score", color_column="cohort")
ch2.style.color_palette.reset_palette_order()
ch2.plot.histogram(values, values_column="score", color_column="cohort", method="density")
```

For 2D density:

```python
points = pd.DataFrame({"x": [0.0, 0.2, 0.8, 1.1], "y": [0.1, 0.3, 0.9, 1.0]})
ch = chartify.Chart(blank_labels=True, x_axis_type="density", y_axis_type="density")
ch.plot.hexbin(points, x_values_column="x", y_values_column="y", size=0.5)
```

## 5. Radar Area / Perimeter / Radius

Radar row order defines vertex order. Sort each series to the same metric order before plotting.

```python
import pandas as pd
import chartify

metrics = ["speed", "quality", "cost", "reliability"]
radar_df = pd.DataFrame({
    "metric": metrics * 2,
    "model": ["baseline"] * 4 + ["candidate"] * 4,
    "score": [0.6, 0.8, 0.5, 0.7, 0.7, 0.9, 0.4, 0.8],
})
radar_df["metric"] = pd.Categorical(radar_df["metric"], categories=metrics, ordered=True)
radar_df = radar_df.sort_values(["model", "metric"])

radar = chartify.RadarChart(blank_labels=True, layout="slide_50%")
radar.plot.area(radar_df, radius_column="score", color_column="model", alpha=0.25)
radar.plot.perimeter(radar_df, radius_column="score", color_column="model", line_width=2)
radar.set_title("Model comparison")
radar.set_legend_location("outside_bottom")
```

If you add metric text, use a one-row-per-vertex DataFrame and `radar.plot.text(labels, "score", text_column="metric", text_align="center")`.

## 6. Second Y-Axis Chart with HTML Export Caveat

A second axis is only available for numeric/log y-axis charts. Save HTML for a portable smoke check; PNG/SVG additionally need a Selenium browser driver.

```python
import pandas as pd
import chartify

df = pd.DataFrame({
    "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
    "orders": [100, 120, 150],
    "revenue": [10_000, 13_000, 18_000],
})

ch = chartify.Chart(blank_labels=True, x_axis_type="datetime", y_axis_type="linear", second_y_axis=True)
ch.plot.line(df, x_column="date", y_column="orders")
ch.axes.set_yaxis_label("Orders")

ch.second_axis.plot.line(df, x_column="date", y_column="revenue", line_dash="dashed")
ch.second_axis.axes.set_yaxis_label("Revenue")

ch.set_title("Orders and revenue")
ch.save("orders_revenue.html", format="html")
```

Do not use `second_y_axis=True` with categorical or density y-axes; Chartify rejects those combinations during `Chart(...)` construction.

## 7. Data Inspection Before Returning a Chart

```python
sources = ch.data
for source in sources:
    print(sorted(source.keys()))
```

`ch.data` returns the plotted Bokeh data sources as dictionaries. For color-grouped numeric charts, expect one source per color factor. For categorical bars, expect a source containing `"factors"` and the numeric column. Use this inspection to catch empty frames, wrong column names, or unintended grouping before saving.

## 8. Show and Save Output

```python
# In notebooks or interactive contexts:
ch.show("html")

# In scripts and automated smoke checks:
ch.save("chart.html", format="html")

# Optional final image exports; require a working browser driver:
ch.save("chart.png", format="png")
ch.save("chart.svg", format="svg")
```

Prefer HTML for CI or headless environments unless the browser/driver stack is confirmed.
