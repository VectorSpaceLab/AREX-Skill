# Basic Chartify API Reference

Evidence distilled from Chartify public package exports, core source, examples, and tests. This file is self-contained for runtime use; do not rely on external docs while using the generated skill.

## Imports and Constructors

```python
import pandas as pd
import chartify

ch = chartify.Chart(
    blank_labels=False,
    layout="slide_100%",
    x_axis_type="linear",
    y_axis_type="linear",
    second_y_axis=False,
)
radar = chartify.RadarChart(blank_labels=False, layout="slide_50%")
```

### `chartify.Chart(...)`

| Argument | Values / default | Use |
|---|---|---|
| `blank_labels` | `False` by default | `True` starts with empty title, subtitle, axis labels, and source label; useful for programmatic or smoke-test charts. |
| `layout` | `"slide_100%"`, `"slide_75%"`, `"slide_50%"`, `"slide_25%"` | Controls Bokeh figure dimensions through Chartify style defaults. |
| `x_axis_type` | `"linear"`, `"log"`, `"datetime"`, `"categorical"`, `"density"`; default `"linear"` | Determines the x-axis implementation and available `ch.plot` methods. |
| `y_axis_type` | `"linear"`, `"log"`, `"categorical"`, `"density"`; default `"linear"` | Determines the y-axis implementation and available `ch.plot` methods. |
| `second_y_axis` | `False` by default | When `True`, creates `ch.second_axis.axes` and `ch.second_axis.plot`. Only valid when `y_axis_type` is `"linear"` or `"log"`. |

### `chartify.RadarChart(...)`

| Argument | Values / default | Use |
|---|---|---|
| `blank_labels` | `False` by default | Same label behavior as `Chart`. |
| `layout` | Default `"slide_50%"` | Radar charts default to a smaller slide layout. |

Radar charts plot each vertex counter-clockwise starting from the top. The row order in each radar series is therefore meaningful.

## Chart Object Methods and Properties

| Member | Signature / shape | Use |
|---|---|---|
| `ch.set_title(title)` | `title: str -> ch` | Set the main title; returns the chart for chaining. |
| `ch.set_subtitle(subtitle)` | `subtitle: str -> ch` | Set or clear the subtitle (`""` clears it); returns the chart. |
| `ch.set_source_label(source)` | `source: str -> ch` | Set source/footer text; returns the chart. |
| `ch.set_legend_location(location, orientation="horizontal")` | `location` can be `"outside_top"`, `"outside_bottom"`, `"outside_right"`, Bokeh in-plot legend positions such as `"top_right"`, a coordinate tuple, or `None`; `orientation` is `"horizontal"` or `"vertical"` | Set this after plotting grouped/color data. `None` hides the legend. |
| `ch.show(format="html")` | `format` is `"html"`, `"png"`, or `"svg"` | Display a chart. `html` uses Bokeh HTML. `png`/`svg` require a working Selenium browser driver. |
| `ch.save(filename, format="html")` | `filename: str`, `format` is `"html"`, `"png"`, or `"svg"` | Save a chart. HTML is the safest portable smoke check; PNG/SVG need a browser driver. Returns the chart. |
| `ch.data` | property returning `list[dict]` | Inspect plotted `ColumnDataSource.data` dictionaries. Multi-series charts generally produce one data dictionary per series. |
| `ch.figure` | Bokeh figure | Escape hatch for low-level Bokeh inspection or customization when Chartify methods are insufficient. |
| `ch.plot` | plot-method namespace | Methods depend on axis-type routing below. |
| `ch.axes` | axis-method namespace | Basic label/range/format methods live here; advanced axis formatting routes to `styling-annotations`. |
| `ch.callout` | callout namespace | Callout-focused annotation routes to `styling-annotations`. |

## Axis-Type to Plot-Method Routing

Chartify exposes different `ch.plot` methods based on `x_axis_type` and `y_axis_type`. If a method is missing, the axis combination is usually wrong.

| Axis configuration | Plot namespace | Methods | Main data arguments |
|---|---|---|---|
| `Chart(x_axis_type="linear"|"log"|"datetime", y_axis_type="linear"|"log")` | numeric/datetime x with numeric y | `line`, `scatter`, `text`, `area` | `data_frame`, `x_column`, `y_column`; optional `color_column`/`color_order`; `text` also needs `text_column`; `scatter` can use `size_column`; `area` can use `second_y_column` and `stacked`. |
| `Chart(x_axis_type="categorical", y_axis_type="linear"|"log")` | vertical mixed categorical/numeric | `bar`, `bar_stacked`, `boxplot`, `interval`, `lollipop`, `parallel`, `scatter`, `text`, `text_stacked` | `data_frame`, `categorical_columns` (string or list), `numeric_column` or bounds columns; optional color/stack/order arguments. |
| `Chart(x_axis_type="linear"|"log", y_axis_type="categorical")` | horizontal mixed categorical/numeric | same mixed methods as above | Same signatures; categorical values render on the y-axis and numeric values on the x-axis. |
| `Chart(x_axis_type="categorical", y_axis_type="categorical")` | categorical heatmap | `heatmap` | `data_frame`, `x_column`, `y_column`, `color_column`; optional `text_column`, palette, text color, and color range. |
| `Chart(y_axis_type="density")` | vertical density histogram/KDE | `histogram`, `kde` | `data_frame`, `values_column`; optional `color_column`, `color_order`, `method`, `bins`. |
| `Chart(x_axis_type="density")` | horizontal density histogram/KDE | `histogram`, `kde` | Same signatures; orientation flips. |
| `Chart(x_axis_type="density", y_axis_type="density")` | 2D density | `hexbin` | `data_frame`, `x_values_column`, `y_values_column`, `size`; optional palette/orientation/range. |
| `Chart(..., second_y_axis=True)` with `y_axis_type="linear"|"log"` | second numeric y-axis | first axis: `ch.plot.*`; second axis: `ch.second_axis.plot.line`, `scatter`, `text`, `area` | Use the same numeric/datetime signatures. Format the right axis with `ch.second_axis.axes.*`. |
| `RadarChart(...)` | radar | `area`, `perimeter`, `radius`, `text` | `data_frame`, `radius_column`; optional `color_column`, `color_order`; `text` also needs `text_column`. |

Unsupported or easy-to-miss combinations:

- `Chart(x_axis_type="datetime", y_axis_type="density")` is not implemented.
- `second_y_axis=True` is rejected for categorical or density y-axes.
- A plot method not shown for the selected axis types raises an `AttributeError` with guidance to change `x_axis_type`/`y_axis_type`.

## Common Plot Signatures

### Numeric/datetime x, numeric y

```python
ch.plot.line(data_frame, x_column, y_column,
             color_column=None, color_order=None,
             line_dash="solid", line_width=4, alpha=1.0)

ch.plot.scatter(data_frame, x_column, y_column,
                size_column=None, color_column=None, color_order=None,
                alpha=1.0, marker="circle")

ch.plot.text(data_frame, x_column, y_column, text_column,
             color_column=None, color_order=None,
             font_size="1em", x_offset=0, y_offset=0,
             angle=0, text_color=None)

ch.plot.area(data_frame, x_column, y_column,
             second_y_column=None, color_column=None, color_order=None,
             stacked=False)
```

Use `x_axis_type="datetime"` for datetime x data. Chartify casts convertible datetime strings to `datetime64[ns]` for datetime x-axis numeric plot methods. Sort line/area data by the x column yourself.

### Mixed categorical/numeric

```python
ch.plot.bar(data_frame, categorical_columns, numeric_column,
            color_column=None, color_order=None,
            categorical_order_by="values", categorical_order_ascending=False)

ch.plot.bar_stacked(data_frame, categorical_columns, numeric_column, stack_column,
                    normalize=False, stack_order=None,
                    categorical_order_by="values", categorical_order_ascending=False)

ch.plot.boxplot(data_frame, categorical_columns, numeric_column,
                color_column=None, color_order=None,
                categorical_order_by="labels", categorical_order_ascending=True,
                outlier_marker="circle", outlier_color="black",
                outlier_alpha=0.3, outlier_size=15)

ch.plot.interval(data_frame, categorical_columns,
                 lower_bound_column, upper_bound_column, middle_column=None,
                 categorical_order_by="values", categorical_order_ascending=False,
                 color="black")

ch.plot.lollipop(data_frame, categorical_columns, numeric_column,
                 color_column=None, color_order=None,
                 categorical_order_by="values", categorical_order_ascending=False)

ch.plot.parallel(data_frame, categorical_columns, numeric_column,
                 color_column=None, color_order=None,
                 categorical_order_by="values", categorical_order_ascending=False,
                 line_dash="solid", line_width=4, alpha=1.0)

ch.plot.scatter(data_frame, categorical_columns, numeric_column,
                size_column=None, color_column=None, color_order=None,
                categorical_order_by="count", categorical_order_ascending=False,
                alpha=1.0, marker="circle")

ch.plot.text(data_frame, categorical_columns, numeric_column, text_column,
             color_column=None, color_order=None,
             categorical_order_by="values", categorical_order_ascending=False,
             font_size="1em", x_offset=0, y_offset=0,
             angle=0, text_color=None)

ch.plot.text_stacked(data_frame, categorical_columns, numeric_column,
                     stack_column, text_column,
                     normalize=False, stack_order=None,
                     categorical_order_by="values", categorical_order_ascending=False,
                     font_size="1em", x_offset=0, y_offset=0,
                     angle=0, text_color=None)
```

For `categorical_columns`, pass a string for one categorical level or a list for grouped/multi-factor categories. Aggregate duplicate category combinations before plotting bars, stacks, intervals, lollipops, parallel plots, and categorical text.

### Heatmap

```python
ch = chartify.Chart(blank_labels=True,
                    x_axis_type="categorical",
                    y_axis_type="categorical")
ch.plot.heatmap(data_frame, x_column, y_column, color_column,
                text_column=None, color_palette="RdBu",
                reverse_color_order=False, text_color="white",
                text_format="{:,.2f}",
                color_value_min=None, color_value_max=None,
                color_value_range=100)
```

`x_column` and `y_column` are categorical dimensions; `color_column` is the numeric cell value. If you pass `text_column`, values are formatted inside the heatmap cells.

### Density

```python
ch.plot.histogram(data_frame, values_column,
                  color_column=None, color_order=None,
                  method="count", bins="auto")

ch.plot.kde(data_frame, values_column,
            color_column=None, color_order=None)

ch.plot.hexbin(data_frame, x_values_column, y_values_column, size,
               color_palette="Blues", reverse_color_order=False,
               orientation="pointytop", color_value_range=10)
```

`histogram(..., method="count")` counts observations per bin. `method="density"` makes the histogram compatible with overlaid KDE curves. `hexbin` needs both axes set to `"density"` and a bin `size`.

### Radar

```python
radar = chartify.RadarChart(blank_labels=True, layout="slide_50%")
radar.plot.area(data_frame, radius_column,
                color_column=None, color_order=None, alpha=0.2)
radar.plot.perimeter(data_frame, radius_column,
                     color_column=None, color_order=None,
                     line_dash="solid", line_width=4, alpha=1.0)
radar.plot.radius(data_frame, radius_column,
                  color_column=None, color_order=None,
                  line_dash="solid", line_width=4, alpha=1.0)
radar.plot.text(data_frame, radius_column, text_column,
                color_column=None, color_order=None,
                font_size="1em", x_offset=0, y_offset=0,
                angle=0, text_color=None, text_align="left")
```

Radar methods transform each row's `radius_column` value into x/y coordinates. When `color_column` is provided, each factor becomes one radar series; each factor should have the same ordered sequence of vertices for meaningful comparison.

## Labeling, Legend, Data, and Output Basics

```python
ch = chartify.Chart(blank_labels=True, x_axis_type="datetime")
ch.plot.line(df.sort_values("date"), "date", "total", color_column="segment")
ch.set_title("Monthly total")
ch.set_subtitle("Grouped by segment")
ch.set_source_label("Source: internal DataFrame")
ch.set_legend_location("outside_bottom")

plotted_sources = ch.data
ch.save("monthly_total.html", format="html")
# ch.show("html")        # interactive display
# ch.save("plot.png", format="png")  # requires Selenium browser driver
# ch.save("plot.svg", format="svg")  # requires Selenium browser driver
```

`Chart.save(..., format="html")` is the safest output smoke check because it does not require a system browser driver. PNG and SVG rendering use Selenium to drive a headless browser.
