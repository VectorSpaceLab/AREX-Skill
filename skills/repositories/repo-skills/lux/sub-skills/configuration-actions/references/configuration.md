# Lux configuration operating reference

Lux exposes one global configuration object, `lux.config`, for the current Python process. These settings affect all Lux dataframes created or displayed in the session. Configuration is not stored per dataframe unless recommendations have already been cached on that dataframe.

## Safe configuration pattern

```python
import lux
import pandas as pd

lux.config.set_executor_type("Pandas")   # base dataframe workflow
lux.config.default_display = "lux"       # or "pandas"
lux.config.plotting_backend = "vegalite" # or "altair" / "matplotlib"
lux.config.topk = 8

df = pd.DataFrame({
    "group": ["A", "A", "B", "B", "C", "C"],
    "x": [1, 2, 3, 4, 5, 6],
    "y": [2, 3, 5, 7, 11, 13],
})
df.intent = ["group", "x"]
df
```

If `df` has already generated recommendations, refresh them before relying on new configuration:

```python
lux.config.plotting_backend = "matplotlib"
lux.config.plotting_style = None
# Force cached recommendations/widgets to be rebuilt on next display.
df.expire_recs()
df
```

For multiple dataframes, call `expire_recs()` on each dataframe whose displayed recommendations should be regenerated. If a change affects metadata or semantic data types rather than recommendation display, use the data-type sub-skill for `expire_metadata()` guidance.

## `lux.config` option map

Defaults can vary across Lux builds, so query the current value (`lux.config.topk`, etc.) before reporting a default to a user. The behavior below is verified for Lux API 0.5.1.

| Option | Accepted values | Effect | Invalid-value behavior |
| --- | --- | --- | --- |
| `default_display` | String `"lux"` or `"pandas"`, case-insensitive | Chooses whether notebook dataframe display opens on the Lux widget or Pandas table. Users can still toggle in the widget. | Unsupported strings warn and preserve the previous value. Non-string values can fail before the warning because the setter lowercases the input. |
| `plotting_backend` | `"vegalite"`, `"altair"`, or `"matplotlib"`, case-insensitive | Chooses the renderer for charts in the Lux widget and influences the backend used by code export. `"altair"` maps to the Vega-Lite/Altair renderer. `"matplotlib"` stores an internal value equivalent to Matplotlib SVG rendering. | Unsupported strings warn and preserve the previous value. Non-string values can fail before the warning. |
| `plotting_style` | A callable or `None` | Applies a global chart-styling function to every rendered chart for the active backend. | No setter validation; bad callables fail later during rendering/export. |
| `plotting_scale` | Positive float; integers are coerced to float | Multiplies displayed chart width and height. Values below 1 shrink charts; values above 1 enlarge charts. | Non-positive or non-float values warn and preserve the previous value. |
| `topk` | Integer `k` or `False` | Limits each recommendation action tab to the top `k` visualizations. `False` disables top-k pruning and may produce many charts. | Other types warn and preserve the previous value. Avoid `True`; it is accepted as a boolean but is not useful as a top-k cutoff. |
| `sort` | String `"descending"`, `"ascending"`, or `"none"` | Sorts each recommendation action by interestingness score, reverses the ranking, or preserves generation order. | Unsupported strings warn and preserve the previous value. Non-string values can fail before the warning. |
| `number_of_bars` | Integer | Maximum number of bars shown in bar charts; remaining categories are summarized rather than all drawn. | Non-integers warn and preserve the previous value. |
| `label_len` | Integer | Maximum axis-label length before Lux abbreviates long labels. | Non-integers warn and preserve the previous value. |
| `sampling` | Boolean | Enables or disables random sampling for large dataframes. Disable only when the full dataset is small enough to visualize. | Non-booleans warn and preserve the previous value. |
| `sampling_start` | Integer no larger than `sampling_cap` | Row-count threshold at which Lux begins sampling. | Non-integers warn; values above the current cap raise an assertion error. |
| `sampling_cap` | Integer no smaller than `sampling_start` | Maximum number of rows sampled for visualization when sampling is active. | Non-integers warn; values below the current start threshold raise an assertion error. |
| `heatmap` | Boolean | Enables replacing large scatterplots with heatmaps for performance. | Non-booleans warn and preserve the previous value. |
| `heatmap_bin_size` | Integer attribute | Sets the N-by-N bin resolution used for generated heatmaps. The inspected build initializes this to `40`. | No validated property setter; use a positive integer to avoid downstream rendering errors. |
| `pandas_fallback` | Boolean | When Lux display logic fails, `True` falls back to normal Pandas display; `False` exposes errors for debugging. | Non-booleans warn and preserve the previous value. |
| `interestingness_fallback` | Boolean | When interestingness scoring fails, `True` falls back instead of raising; `False` exposes scoring errors. | Non-booleans warn and preserve the previous value. |

## Plotting styles

`plotting_style` must match the active backend.

Altair/Vega-Lite style functions take one chart object and return the chart:

```python
lux.config.plotting_backend = "vegalite"

def make_green(chart):
    chart = chart.configure_mark(color="green")
    chart.title = "Custom Title"
    return chart

lux.config.plotting_style = make_green
df.expire_recs()
df
```

Matplotlib style functions take `(fig, ax)` and return the updated objects:

```python
lux.config.plotting_backend = "matplotlib"

def widen_and_title(fig, ax):
    fig.set_figwidth(7)
    ax.set_title("Custom Title")
    return fig, ax

lux.config.plotting_style = widen_and_title
df.expire_recs()
df
```

If exported chart code is the user's main goal, route to `visualization-export`; this sub-skill only sets the global backend/style.

## Sampling, heatmaps, top-k, and sort

Use these settings before first display when possible:

```python
lux.config.sampling = True
lux.config.sampling_start = 20_000
lux.config.sampling_cap = 40_000
lux.config.heatmap = True
lux.config.heatmap_bin_size = 50
lux.config.sort = "descending"
lux.config.topk = 10
```

Maintain the `sampling_start <= sampling_cap` invariant at every assignment. If lowering both values, lower `sampling_start` first, then `sampling_cap`. If raising both values, raise `sampling_cap` first when needed.

## Executor selection

For ordinary Pandas-backed dataframes, use:

```python
lux.config.set_executor_type("Pandas")
```

`set_executor_type("Pandas")` resets SQL connection state and installs the Pandas executor. `set_executor_type("SQL")` initializes the SQL executor and query templates, but actual SQL connection and table setup belong in `sql-backend`. Any executor value other than exact `"Pandas"` or exact `"SQL"` raises `ValueError`.
