# Custom charts

This page covers the SwanLab chart namespace, text-table wrapper, and the lightweight plot helpers.

## When to use what

| Goal | Use | Why |
|---|---|---|
| A standard pyecharts chart | `swanlab.ECharts(chart)` or `swanlab.log_echarts(...)` | Any object with `dump_options()` is accepted. |
| A pure text table | `swanlab.echarts.Table` | SwanLab's wrapper serializes headers and rows into chart options. |
| ROC, PR, or confusion-matrix charts | `swanlab.plot.roc_curve`, `swanlab.plot.pr_curve`, `swanlab.plot.confusion_matrix` | Convenience builders that return pyecharts charts. |

## `swanlab.echarts`

The `swanlab.echarts` namespace exposes the pyecharts chart classes plus SwanLab helpers.

Typical flow:

```python
import swanlab

chart = swanlab.echarts.Bar().add_xaxis(["a", "b"]).add_yaxis("series", [1, 2])
swanlab.log_echarts(key="bar", data=chart)
```

## `swanlab.ECharts`

`ECharts(chart, caption=None)` is the media wrapper around a pyecharts chart object.

Use it when you want to:

- keep a chart object separate from the logging call,
- attach a caption to a chart,
- reuse the same chart object across different code paths.

The only hard requirement is `dump_options()`.
If the object does not provide that method, SwanLab rejects it with a type error.

## `swanlab.echarts.Table`

`Table` is SwanLab's text-table chart wrapper.

Behavior to remember:

- `add(headers, rows, attributes=None, **kwargs)` records the table data and returns the table object.
- `dump_options()` converts the table into JSON options.
- `headers` become `colDefs`.
- `rows` become `rowData`.
- `set_global_opts(...)` is intentionally not supported.

This is the right choice for compact experiment summaries, leaderboard-style views, and other text-first reports.

## `swanlab.plot`

`plot` is a helper namespace for common diagnostic charts.

It currently exposes:

- `roc_curve`
- `pr_curve`
- `confusion_matrix`

These helpers return pyecharts chart objects; they are not logging calls.
They depend on pyecharts and scikit-learn, so skip them when those packages are missing.
A common pattern is:

```python
chart = swanlab.plot.roc_curve(y_true, y_score, title=True)
swanlab.log_echarts(key="roc", data=chart)
```

## Selection rules

- If the user already has a chart object, log it directly with `log_echarts` or wrap it in `ECharts`.
- If the user needs a table-only report, prefer `swanlab.echarts.Table` over a plain dictionary.
- If the user needs a ready-made diagnostic chart, prefer `swanlab.plot`.
- If the request is really about scalar metrics, route back to `experiment-tracking`.
- If the request comes from a framework callback or plugin, route back to `integrations-and-plugins`.
