# Workflows

These workflows stay inside the styling and annotation surface. If you still need to choose a plot family or reshape data first, switch to `../basic-charting/SKILL.md`.

## 1) Add labels and legend placement

1. Create the chart and plot the data first.
2. Set the title, subtitle, and source label after plotting.
3. Move or hide the legend only after the plot has created one.
4. Use `outside_bottom` or `outside_right` when the legend should sit outside the plotting area.

```python
import chartify

ch = chartify.Chart(blank_labels=True)
ch.plot.scatter(data_frame=df, x_column="x", y_column="y", color_column="group")
ch.set_title("Headline")
ch.set_subtitle("Short data description")
ch.set_source_label("Internal analysis")
ch.set_legend_location("outside_bottom", orientation="horizontal")
```

## 2) Format axes and factor order

1. Decide whether the axis is numeric, datetime, or categorical.
2. Apply ranges and tick values before or after plotting, depending on whether the data limits are already known.
3. Use date-format strings for datetime x-axis tick labels and numeric format strings for numeric axes.
4. For grouped categorical axes, prefer plot-time ordering first; use axis factor setters when you need a post-hoc override.
5. If grouped labels are present, pass a list to the tick-orientation setter so each hierarchy level can rotate independently.

```python
import pandas as pd

ch = chartify.Chart(x_axis_type="datetime")
ch.plot.line(df, x_column="date", y_column="value")
ch.axes.set_xaxis_range(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31"))
ch.axes.set_xaxis_tick_values(pd.date_range("2024-01-01", "2024-12-01", freq="MS"))
ch.axes.set_xaxis_tick_format("%Y-%m")

ch = chartify.Chart(x_axis_type="categorical")
ch.plot.bar(df, categorical_columns=["group", "subgroup"], numeric_column="value")
ch.axes.set_xaxis_factors([("A", "one"), ("A", "two"), ("B", "one")])
ch.axes.set_xaxis_tick_orientation(["vertical", "horizontal", "diagonal"])
```

## 3) Add callouts

1. Use `line` for horizontal or vertical spans.
2. Use `line_segment` for a specific segment between two points.
3. Use `box` for highlighted regions.
4. Use `text` for narrative annotations.
5. On datetime axes, pass datetime-like x-side values and let the helper convert them to epoch milliseconds.

```python
import chartify

ch = chartify.Chart(blank_labels=True, x_axis_type="datetime")
ch.plot.line(df.sort_values("date"), x_column="date", y_column="value")
ch.callout.line("2024-03-01", orientation="height", line_width=6)
ch.callout.line_segment("2024-02-01", 10, "2024-04-01", 20)
ch.callout.box(top=25, bottom=5, left="2024-02-15", right="2024-03-15")
ch.callout.text("Peak period", "2024-03-01", 22)
```

## 4) Choose palettes and apply config

1. Pick a palette type that matches the meaning of the color dimension.
2. Use `accent_values` when only certain values should receive special colors.
3. Register custom palettes with `create_palette`, then reference them by name in `set_color_palette`.
4. If a palette needs more colors, try `sort_by_*`, `expand_palette`, or `shift_palette` to tune the palette before using it.
5. When a config directory is involved, set `CHARTIFY_CONFIG_DIR` before importing `chartify`.

```python
import chartify

chartify.color_palettes.create_palette(["#ff0000", "#ffaa00", "#0066ff"], "categorical", "demo palette")

ch = chartify.Chart(blank_labels=True)
ch.style.set_color_palette("categorical", "demo palette")
ch.style.set_color_palette("accent", accent_values={"US": "red", "CA": "blue"})
```

## 5) Work with style settings YAML

1. Put trusted YAML files under one config directory.
2. Use `options_config.yaml` for default palette names and blank-label behavior.
3. Use `style_settings_config.yaml` for figure, legend, subtitle, interval, line, and second-axis style values.
4. Use `colors_config.yaml` only for trusted custom color-name mappings because it uses `UnsafeLoader`.
5. Use `color_palettes_config.yaml` for custom palette registries.

```python
import os

os.environ["CHARTIFY_CONFIG_DIR"] = "/tmp/chartify-config/"
import chartify
```

## RadarChart reminder

`RadarChart` uses the same label, axis, callout, style, and palette APIs as `Chart`. The only default difference you usually need to remember is the compact `slide_50%` layout.
