# Styling and Annotation API Reference

This sub-skill starts after plot-family selection. If you still need to choose a plot method or reshape a DataFrame, use `../basic-charting/SKILL.md`.

## Chart and RadarChart

| API | Use |
| --- | --- |
| `chartify.Chart(blank_labels=False, layout='slide_100%', x_axis_type='linear', y_axis_type='linear', second_y_axis=False)` | Main chart class for labels, axes, legend control, callouts, style updates, and optional second y axis. |
| `chartify.RadarChart(blank_labels=False, layout='slide_50%')` | Radar chart with the same styling surface and a smaller default layout. |

`blank_labels=True` starts with empty title, subtitle, axis labels, and source label. `RadarChart` usually uses the same annotation and palette workflow as `Chart`.

## Label and legend APIs

| API | Notes |
| --- | --- |
| `set_title(title)` | Set the chart title and return the current chart. |
| `set_subtitle(subtitle)` | Set or clear the subtitle. Pass `""` to remove it. |
| `set_source_label(source)` | Set footer/source text and return the current chart. |
| `set_legend_location(location, orientation="horizontal")` | Move or hide the legend and return the current chart. `location` may be `outside_top`, `outside_bottom`, `outside_right`, a Bokeh in-plot legend location such as `top_right`, a coordinate tuple, or `None`. `orientation` may be `horizontal` or `vertical`. |

Legend notes:

- Call `set_legend_location(...)` after plotting grouped or color-separated data so a legend exists.
- `None` hides the legend instead of deleting it.
- Outside placements move the legend into the figure layout.
- Vertical legend placement reverses stacked-series order so the legend matches the visual stack.

## Axis APIs

### Numeric and datetime axes

Use these on `NumericalXYAxes`, `NumericalXAxis`, `NumericalYAxis`, `DatetimeXNumericalYAxes`, and `SecondYNumericalAxis` as appropriate.

| API | Notes |
| --- | --- |
| `set_xaxis_range(start=None, end=None)` / `set_yaxis_range(start=None, end=None)` | Set the visible range on numeric or datetime axes. Datetime x axes accept strings or `pd.Timestamp` values and convert them to epoch milliseconds. |
| `set_xaxis_tick_values(values)` / `set_yaxis_tick_values(values)` | Pin tick locations with numeric values or a `DatetimeIndex` on datetime x axes. |
| `set_xaxis_tick_format(num_format)` | Format x ticks with Numbro-style numeric strings such as `0.00%`, `$0,0.00`, or `0 a`. On datetime x axes, use date-format strings such as `%Y-%m`. |
| `set_yaxis_tick_format(num_format)` | Format y ticks with Numbro-style numeric strings. |
| `hide_xaxis()` / `hide_yaxis()` | Hide ticks, tick labels, and axis lines while leaving the axis label visible until you clear it. |

Datetime-specific notes:

- Chartify casts convertible datetime strings to `datetime64[ns]` for datetime x-axis numeric plot methods.
- `set_xaxis_range(...)` and `set_xaxis_tick_values(...)` both convert datetime-like input to epoch milliseconds.
- Sort line and area data by the x column yourself before plotting.

### Categorical axes and factor order

Use these on `NumericalXAxis`, `NumericalYAxis`, and `CategoricalXYAxes`.

| API | Notes |
| --- | --- |
| `set_xaxis_factors(factors)` / `set_yaxis_factors(factors)` | Set explicit categorical factor order. `factors` may be a list, `pd.Index`, or `MultiIndex`. |
| `set_xaxis_tick_orientation(orientation='horizontal')` / `set_yaxis_tick_orientation(orientation='horizontal')` | Rotate major, subgroup, and group labels. Pass a single value or a list of up to three values. Allowed values are `horizontal`, `vertical`, and `diagonal`. |

Categorical ordering notes:

- Plot-time ordering parameters such as `categorical_order_by` and `categorical_order_ascending` usually come first.
- Use axis factor setters when you need a post-hoc override or hand-authored ordering.
- Grouped categorical labels can interpret orientation differently on x and y axes, so test the hierarchy you are rotating.

### Second y axis

`SecondYNumericalAxis` exposes the same numeric y-axis controls as the primary axis:

- `set_yaxis_range(start=None, end=None)`
- `set_yaxis_label(label)`
- `set_yaxis_tick_format(num_format)`
- `set_yaxis_tick_values(values)`

## Callout APIs

| API | Notes |
| --- | --- |
| `line(location, orientation='width', ...)` | Add a Bokeh span. On datetime x axes, `orientation='height'` converts `location` to epoch milliseconds. |
| `line_segment(x_start, y_start, x_end, y_end, ...)` | Add an arrow-style segment. On datetime x axes, both x coordinates are converted to epoch milliseconds. |
| `box(top=None, bottom=None, left=None, right=None, ...)` | Add a shaded box. On datetime x axes, `left` and `right` are converted to epoch milliseconds. |
| `text(text, x, y, ...)` | Add annotation text. On datetime x axes, the x coordinate is converted to epoch milliseconds. |

Callout notes:

- Datetime callout helpers accept strings or `pd.Timestamp` values, so ISO date strings work in tests and scripts.
- `text` uses the chart's configured callout font.
- Keep y coordinates numeric; only the time axis values are converted on datetime charts.

## Style, palettes, and options

### Palette selection

| API | Notes |
| --- | --- |
| `style.set_color_palette(palette_type, palette=None, accent_values=None)` | Select palette behavior for `categorical`, `sequential`, `diverging`, or `accent` use cases. |
| `chartify.color_palettes.create_palette(colors, palette_type, name)` | Register a custom palette in the global registry so later charts can select it by name. |
| `chartify.color_palettes['name']` | Case-insensitive palette lookup. Raises `KeyError` when the name is missing. |

`palette` may be a palette name, a `ColorPalette`, or a list of color strings. `accent_values` may be a list of values or a dict mapping values to explicit colors. `accent` palettes use the default color from `style.color_palette_accent_default_color` for values that are not accented.

### Built-in palette names

| Name | Kind |
| --- | --- |
| `Category20` | categorical |
| `Category10` | categorical |
| `Colorblind` | categorical |
| `Dark2` | categorical |
| `Pastel1` | categorical |
| `RdBu` | diverging |
| `RdGy` | diverging |
| `Greys` | sequential |
| `Greens` | sequential |
| `Blues` | sequential |
| `Reds` | sequential |
| `Oranges` | sequential |
| `All colors` | categorical |

### Palette utilities

| API | Notes |
| --- | --- |
| `sort_by_hue(ascending=True)` | Return a new palette sorted by hue. |
| `sort_by_luminance(ascending=True)` | Return a new palette sorted by luminance. |
| `sort_by_saturation(ascending=True)` | Return a new palette sorted by saturation. |
| `expand_palette(target_color_count)` | Linearly expand a palette to a larger color count. Start from a palette with at least two colors. |
| `shift_palette(target_color, percent=10)` | Shift each palette color toward another color. |
| `reset_palette_order()` | Reset ordered palettes to their starting cycle before repeating a plot. |

### Options API

| API | Notes |
| --- | --- |
| `chartify.options.get_option(option_name)` | Read a global option value. |
| `chartify.options.set_option(option_name, option_value)` | Mutate a global option value before building charts. |

Default option keys:

- `style.color_palette_categorical`
- `style.color_palette_sequential`
- `style.color_palette_diverging`
- `style.color_palette_accent`
- `style.color_palette_accent_default_color`
- `chart.blank_labels`
- `config.logos_path`
- `config.options`
- `config.style_settings`
- `config.colors`
- `config.color_palettes`

Config safety note: `options_config.yaml` and `colors_config.yaml` are loaded with `yaml.UnsafeLoader`, so only use trusted files.
