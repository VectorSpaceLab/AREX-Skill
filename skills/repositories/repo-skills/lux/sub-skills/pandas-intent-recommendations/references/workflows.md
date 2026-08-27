# Pandas intent and recommendation workflows

This reference covers Lux's Pandas-integrated dataframe workflow. It assumes the package import module is `lux` and the installed distribution is `lux-api`.

## 1. Enable Lux before dataframe creation

Lux activates by importing `lux`. The import registers default recommendation actions and monkeypatches Pandas constructors so new `pd.DataFrame`, `pd.Series`, and common `pd.read_*` results are Lux subclasses.

```python
import lux
import pandas as pd

df = pd.DataFrame({
    "sales": [10, 13, 15, 20, 21, 25],
    "profit": [1, 2, 1, 4, 3, 5],
    "region": ["West", "West", "East", "East", "North", "North"],
})
print(type(df))  # lux.core.frame.LuxDataFrame
```

Operational rules:

- Importing Pandas before Lux is acceptable only if the dataframe is created after `import lux`; already-created plain Pandas objects do not retroactively gain Lux metadata.
- Recreate or wrap an old object after importing Lux when Lux attributes are missing: `df = pd.DataFrame(old_df)`.
- `df["col"]` and other Series-producing operations usually return `LuxSeries`, preserving metadata where possible.
- Use `df.to_pandas()` or `series.to_pandas()` when third-party code requires plain Pandas behavior.

## 2. Work without intent: default recommendations

With no user intent, Lux computes default analytical actions when a dataframe is displayed in a notebook or when `df.recommendation` is accessed programmatically.

```python
recs = df.recommendation
print(recs.keys())
```

Default tabs are data-dependent. Possible tabs include:

| Tab | When it appears | Meaning |
| --- | --- | --- |
| `Correlation` | At least two usable quantitative attributes | Pairwise quantitative relationships, ranked by correlation. |
| `Distribution` | Quantitative attributes | Histogram distributions, ranked by skewness. |
| `Occurrence` | Nominal/categorical attributes | Bar charts of category counts, ranked by unevenness. |
| `Temporal` | Temporal attributes or parseable time-related fields | Time-trend line charts and timescale variants. |
| `Geographical` | Geographic semantic fields | Choropleth-style map recommendations; detailed type guidance belongs in `special-data-types`. |

Not every tab appears for every dataframe. Very small, empty, highly identifier-like, or semantically ambiguous data can yield fewer tabs or only warning messages.

## 3. Set dataframe intent

Intent communicates which attributes or values the user wants to inspect. Set it with a list.

```python
# Attribute intent: current visualization is sales vs profit.
df.intent = ["sales", "profit"]

# Filter intent: compare the requested subset while preserving Lux awareness.
df.intent = ["sales", "region=West"]

# OR intent with a pipe or a list.
df.intent = ["sales|profit", "region"]
df.intent = [["sales", "profit"], "region"]
```

Equivalent explicit method:

```python
df.set_intent(["sales", "profit"])
```

Clear intent and return to default recommendations:

```python
df.clear_intent()
```

Use `lux.Clause` only when a concise string is not enough, for example to constrain channels, aggregation, data type, or filter operators. Keep this sub-skill focused on dataframe intent; route detailed `Clause`, `Vis`, and `VisList` construction to `visualization-export`.

```python
import lux

df.intent = [
    lux.Clause(attribute="sales", channel="x"),
    lux.Clause(attribute="profit", channel="y"),
]
```

`df.intent = ...` accepts either a list of strings/clauses or a single `Vis` object. A bare string such as `df.intent = "sales"` raises a type error; use `df.intent = ["sales"]`.

## 4. Understand `current_vis` and intent-specific recommendations

After intent is set, Lux parses, validates, and compiles it into `df.current_vis`.

```python
df.intent = ["sales", "profit"]
current = df.current_vis
print(len(current), current[0].mark)
```

`df.current_vis` is a visualization list representing the current intent. If the intent compiles to exactly one visualization, recommendation tabs usually shift from default exploration to next-step suggestions.

Intent-specific tabs include:

| Tab | Meaning |
| --- | --- |
| `Enhance` | Add another attribute to the current intent, often as a breakdown or additional relationship. |
| `Filter` | Add or vary a filter while holding the selected attributes fixed. |
| `Generalize` | Remove one attribute or filter to show a broader trend. |
| `Similarity` | For suitable line/filter intents, compare visually similar alternatives. |

`df.recommendation` is a dictionary mapping tab names to `VisList` collections:

```python
for tab, vis_list in df.recommendation.items():
    print(tab, len(vis_list))
```

If an intent uses wildcards or OR values and compiles to multiple current visualizations, Lux may show current visualizations rather than all next-step tabs. For detailed multi-visualization handling, use `visualization-export`.

## 5. Set intent from a `Vis`

Use `set_intent_as_vis` when the user already has a Lux `Vis` object and wants the dataframe to adopt that visualization as intent.

```python
from lux.vis.Vis import Vis

vis = Vis(["region", "sales"], df)
df.set_intent_as_vis(vis)
print(df.intent)
print(df.current_vis)
```

This is useful after a user chooses or constructs a candidate visualization and wants Lux to recommend follow-up analyses around it. Detailed `Vis` creation and export remain owned by `visualization-export`.

## 6. Interpret `exported` at a high level

`df.exported` exposes visualizations selected in the Lux widget export UI.

- If no widget has been attached to the dataframe, it warns and returns `[]`.
- If the widget exists but no visualization was selected, it warns and returns `[]` unless a previous selection is saved.
- If selected visualizations all come from one recommendation tab, it returns a `VisList`.
- If selections span multiple tabs, it returns a dictionary such as `{ "Current Vis": VisList(...), "Enhance": VisList(...) }`.

For scripts and non-notebook environments, inspect `df.current_vis` and `df.recommendation` directly. For detailed chart/code export methods (`to_altair`, `to_matplotlib`, `to_vegalite`, `to_code`), route to `visualization-export`.

## 7. Save the widget as HTML

`df.save_as_html(filename="export.html", output=False)` creates a static Lux widget export. If no widget exists yet, Lux tries to compute recommendations and attach one first.

```python
df.intent = ["sales", "profit"]
df.save_as_html("lux-output.html")
html = df.save_as_html(output=True)
```

Caveats:

- HTML export depends on notebook/widget infrastructure and embedded widget state.
- When `output=True`, the method returns the HTML string instead of writing a file.
- If widget setup or frontend rendering fails, use `configuration-actions` troubleshooting.

## 8. Pandas operation caveats

### `head()` and `tail()`

`df.head()` and `df.tail()` return Lux dataframes, but Lux keeps a pointer to the previous dataframe for visualization. Displaying the result tells the user Lux is visualizing the previous version before the `head` or `tail` operation. This avoids misleading recommendations on a tiny truncated sample.

### `groupby()`

`df.groupby(...)` propagates Lux metadata onto the groupby object and marks it as pre-aggregated. Aggregated results can trigger row/column group recommendations instead of the ordinary dataframe tabs. For details about grouped/indexed results, use `special-data-types`.

If you need a groupby operation without appending Lux history, pass `history=False`:

```python
grouped = df.groupby("region", history=False)
```

### Mutations and stale recommendations

Lux expires metadata and recommendations after many Pandas mutations, including setting items or changing axes. If the object still appears stale, explicitly refresh the lazy caches:

```python
df.expire_metadata()
df.expire_recs()
_ = df.recommendation
```

After configuration changes, `df.expire_recs()` is usually enough; use `configuration-actions` for config-specific behavior.

## 9. Offline validation

Use the bundled script to validate that a Lux installation can run this workflow without external files or network access:

```bash
python scripts/intent_recommendation_smoke.py
python scripts/intent_recommendation_smoke.py --help
```

The script creates a small dataframe, checks the Pandas monkeypatch, compiles intent, verifies recommendation dictionaries, confirms current-visualization export facts, and checks the expected `exported` warning in a non-widget context.
