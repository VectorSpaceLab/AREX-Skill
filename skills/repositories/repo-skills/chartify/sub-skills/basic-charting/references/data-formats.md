# Chartify Data Format Rules

Chartify plotting methods expect tidy pandas `DataFrame` inputs with named columns. Most confusing plot failures come from passing grouped Series, leaving category keys in an index, keeping data in a wide/pivoted shape, or choosing axis types that do not match column dtypes.

## Core Tidy Rules

1. Pass a pandas `DataFrame`, not a `Series`, `GroupBy`, NumPy array, or index-only result.
2. Every plotted field must be a named column in `data_frame`.
3. After `groupby`, use `as_index=False` or `.reset_index()`.
4. For wide/pivoted tables, convert to long/tidy form with `pd.melt` or `stack().reset_index(...)`.
5. For categorical mixed-type plots, aggregate to at most one row per required categorical grouping before calling methods that pivot internally.
6. For line and area charts, sort by the x column before plotting.
7. Use `x_axis_type="datetime"` for datetime x values; use numeric dtypes for numeric axes.

## Good GroupBy Patterns

### Single categorical bar

```python
quantity_by_fruit = (
    sales.groupby("fruit", as_index=False)["quantity"]
    .sum()
)

ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
ch.plot.bar(quantity_by_fruit, categorical_columns="fruit", numeric_column="quantity")
```

Equivalent with `.reset_index()`:

```python
quantity_by_fruit = sales.groupby("fruit")["quantity"].sum().reset_index()
```

Do **not** pass `sales.groupby("fruit")["quantity"].sum()` directly; that result puts `fruit` in the index and is not a tidy DataFrame with all fields as named columns.

### Grouped numeric line

```python
monthly = (
    raw.groupby(["date", "segment"], as_index=False)["total"]
    .sum()
    .sort_values("date")
)

ch = chartify.Chart(blank_labels=True, x_axis_type="datetime")
ch.plot.line(monthly, x_column="date", y_column="total", color_column="segment")
```

### Heatmap cell aggregation

```python
heatmap_df = (
    raw.groupby(["fruit", "country"], as_index=False)["price"]
    .mean()
    .rename(columns={"price": "avg_price"})
)

ch = chartify.Chart(blank_labels=True, x_axis_type="categorical", y_axis_type="categorical")
ch.plot.heatmap(heatmap_df, "fruit", "country", "avg_price", text_column="avg_price")
```

## Wide/Pivoted to Long/Tidy

Chartify does not take a pivot table with one series per column for grouped bars or stacked bars. Melt it.

```python
wide = pd.DataFrame({
    "fruit": ["Apple", "Banana"],
    "US": [12, 9],
    "CA": [7, 4],
})

long = pd.melt(
    wide,
    id_vars="fruit",
    var_name="country",
    value_name="quantity",
)
```

Then choose the chart shape:

```python
# grouped categorical bars
ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
ch.plot.bar(long, ["fruit", "country"], "quantity", color_column="country")

# stacked categorical bars
ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
ch.plot.bar_stacked(long, "fruit", "quantity", stack_column="country")
```

## Categorical Columns and Internal Pivoting

Mixed categorical/numeric methods use `categorical_columns` and often pivot internally.

- `categorical_columns="fruit"` creates one categorical level.
- `categorical_columns=["fruit", "country"]` creates grouped/multi-factor categories.
- `bar`, `bar_stacked`, `interval`, `lollipop`, `parallel`, and categorical `text` expect no duplicate rows for the same categorical grouping and stack/color combination after your aggregation.
- `boxplot` intentionally accepts multiple observations per category because it computes quantiles and outliers.
- `scatter` on a categorical axis can accept repeated categories because it plots observations rather than aggregating bars.

If you see an error about each categorical grouping having at most one observation, aggregate first:

```python
clean = (
    raw.groupby(["fruit", "country"], as_index=False)["quantity"]
    .sum()
)
```

Chartify casts categorical factor labels to strings internally for Bokeh compatibility. The original DataFrame dtypes are not overwritten.

## Ordering Categorical Axes

Most categorical methods accept `categorical_order_by` and `categorical_order_ascending`.

| Method family | Useful order values | Notes |
|---|---|---|
| `bar`, `bar_stacked`, `lollipop`, `parallel`, `text`, `text_stacked`, `interval` | `"values"`, `"labels"`, or explicit list/array/Series | `"values"` sorts by numeric totals; `"labels"` sorts by category labels. |
| `scatter` on categorical axis | `"count"`, `"labels"`, or explicit list/array/Series | `"count"` is the default for categorical scatter. |
| `boxplot` | `"labels"` or explicit ordering is safest | It computes distribution summaries rather than simple totals. |

An explicit order must include the labels you intend to render.

## Color, Stack, and Order Columns

`color_column`, `stack_column`, `color_order`, and `stack_order` are common sources of errors.

- `color_column` and `stack_column` must be columns in the passed DataFrame.
- `color_order` must include every unique value present in `color_column` for that plot call.
- `stack_order` must include every distinct value in `stack_column` for stacked bars/text.
- When overlaying multiple plot calls that should reuse the same colors, call `ch.style.color_palette.reset_palette_order()` between calls. Detailed palette work routes to `styling-annotations`, but reset is useful for basic overlays.

## Numeric and Datetime Dtypes

### Datetime x-axis

Use `x_axis_type="datetime"` when plotting date/time values on x:

```python
df["date"] = pd.to_datetime(df["date"])
ch = chartify.Chart(blank_labels=True, x_axis_type="datetime")
ch.plot.line(df.sort_values("date"), "date", "value")
```

Chartify can cast convertible datetime strings to `datetime64[ns]` for datetime x-axis numeric plot methods, but explicit `pd.to_datetime` makes failures clearer.

### Numeric axes

For numeric axes, use numeric pandas dtypes. If a numeric field is object/string, cast it before plotting:

```python
df["value"] = pd.to_numeric(df["value"], errors="raise")
```

If a datetime column is plotted on a non-datetime numeric x-axis, Chartify raises guidance to use `Chart(x_axis_type="datetime")`. If an object dtype is plotted on a numeric x-axis, Chartify raises guidance to adjust axis types or cast input data.

## Radar Data Shape

Radar charts use row order to place vertices counter-clockwise from the top. If comparing series, each `color_column` factor should have the same ordered metrics.

```python
metric_order = ["speed", "quality", "cost", "reliability"]
df["metric"] = pd.Categorical(df["metric"], categories=metric_order, ordered=True)
df = df.sort_values(["model", "metric"])

radar = chartify.RadarChart(blank_labels=True)
radar.plot.area(df, radius_column="score", color_column="model")
```

The `metric` column is not automatically used by `area`, `perimeter`, or `radius`; use `radar.plot.text` with a separate label DataFrame if you want visible metric labels.

## Quick Pre-Plot Checklist

- [ ] Is the object a pandas `DataFrame`?
- [ ] Are all plot arguments named columns in that DataFrame?
- [ ] Did every `groupby` result use `as_index=False` or `.reset_index()`?
- [ ] Did every wide/pivoted table get melted to long form?
- [ ] Do numeric columns have numeric dtypes?
- [ ] Does datetime x data use `x_axis_type="datetime"`?
- [ ] Did categorical bar/stack/interval/lollipop data aggregate duplicate groupings?
- [ ] Do `color_order` and `stack_order` include all present factors?
- [ ] Is line/area data sorted by x?
