# Visualization construction and export workflows

These workflows are self-contained for Lux API 0.5.1. They assume Lux is installed in the active Python environment; they do not require the source repository or any repository data files.

## 1. Minimal setup

Import Lux before creating the dataframe that will be visualized so the Pandas dataframe class is patched to Lux's dataframe subclass.

```python
import lux
import pandas as pd
from lux.vis.Clause import Clause
from lux.vis.Vis import Vis
from lux.vis.VisList import VisList

source = pd.DataFrame(
    {
        "special.char": ["alpha", "beta", "alpha", "gamma"],
        "normal": [1, 2, 3, 4],
        "score": [10, 20, 15, 30],
        "category": ["A", "B", "A", "C"],
    }
)
```

`source` should now be a Lux dataframe. If it was created before importing Lux, recreate it or convert it after importing Lux before relying on recommendation or visualization compilation behavior.

## 2. Build clauses and intents

Lux accepts compact string intents and explicit `Clause` objects.

```python
Clause("normal")                         # shorthand description, parsed later
Clause(attribute="score", channel="x")  # explicit attribute/channel
Clause("category=A")                     # filter shorthand
Clause(attribute="category", value="A") # equivalent explicit filter
Clause(attribute="?", data_model="measure")
```

Useful clause patterns:

- `"attribute"`: visualize one column. A quantitative column usually becomes a histogram; a nominal column usually becomes a bar chart.
- `"attribute=value"`: filter by a categorical value.
- `Clause(attribute=["a", "b"])`: OR over candidate attributes.
- `Clause(value=["A", "B"])`: OR over candidate filter values.
- `Clause(attribute="?", data_type="nominal")`: wildcard over all nominal columns.
- `Clause(attribute="?", data_model="measure")`: wildcard over all quantitative/measure columns.
- `Clause(attribute="?", exclude=["id", "raw_text"])`: wildcard with excluded fields.
- `Clause(attribute="amount", aggregation="sum")`: aggregate a measure. `aggregation=None` means no aggregation for already aggregated data.
- `Clause(attribute="date", timescale="year")`: steer temporal granularity when the column is temporal.

## 3. Construct one visualization with `Vis`

Use `Vis` only when the intent describes exactly one visualization.

```python
vis = Vis([Clause("normal"), Clause("score")], source)
vis.mark        # e.g. "scatter"
vis.data        # processed chart data used by the renderer
vis.intent      # original intent supplied by the user
```

Common inspection helpers:

```python
vis.get_attr_by_attr_name("score")
vis.get_attr_by_channel("x")
vis.get_attr_by_channel("y")
```

Update a `Vis` in place:

```python
vis.set_intent(["category", "score"])
# or
vis.intent = ["category", "score"]
```

Refresh against a new source dataframe with the same relevant schema:

```python
subset = source[source["category"] != "C"]
vis.refresh_source(subset)
```

If the source is missing or stale, exports may be empty or inaccurate. Refresh before exporting after filtering, replacing, or mutating the dataframe.

## 4. Construct visualization collections with `VisList`

Use `VisList` when the intent can expand into multiple visualizations. Wildcard `"?"`, string alternatives containing `"|"`, or list-valued attributes are collection intent, not single-`Vis` intent.

```python
all_against_normal = VisList(["normal", "?"], source)
measure_against_normal = VisList(
    [Clause("normal"), Clause(attribute="?", data_model="measure")],
    source,
)
nominal_against_normal = VisList(
    [Clause("normal"), Clause(attribute="?", data_type="nominal")],
    source,
)
```

You can also compose a collection manually from already specified `Vis` objects:

```python
candidates = [
    Vis([Clause("normal"), Clause("score")]),
    Vis([Clause("category"), Clause("score")]),
]
vislist = VisList(candidates, source)
```

Operate on a `VisList`:

```python
len(vislist)
vislist[0]
list(vislist.map(lambda v: v.mark))
list(vislist.get("score"))
vislist.sort(remove_invalid=True, descending=True)  # in place
vislist.refresh_source(source[source["normal"] >= 2])
```

`normalize_score(invert_order=False)` divides each `Vis.score` by the collection's maximum score and optionally flips the normalized value. Use it only after confirming the maximum score is nonzero.

`showK()` uses `lux.config.topk`: if `topk` is an integer, it returns a new `VisList` containing the first `abs(topk)` visualizations; if `topk` is `False`, it returns the original list. Global top-k and sort configuration belongs to `configuration-actions`.

`set(field_name, field_val)` is present in Lux 0.5.1 but returns `NotImplemented`. To set a field across a collection, loop explicitly:

```python
for v in vislist:
    v.score = 1.0
```

## 5. Export a single `Vis`

Export methods are defined on `Vis`, not on `VisList`. Iterate a collection and export each member separately.

```python
vis = Vis(["normal", "score"], source)

altair_code = vis.to_altair(standalone=False)
matplotlib_code = vis.to_matplotlib()
vegalite_text = vis.to_vegalite(prettyOutput=True)
vegalite_dict = vis.to_vegalite(prettyOutput=False)
```

`to_code(language=...)` dispatches to the backend-specific methods:

```python
vis.to_code(language="altair")
vis.to_code(language="matplotlib")
vis.to_code(language="vegalite")
vis.to_code(language="python")
vis.to_code(language="matplotlib_svg")
```

Use `language="SQL"` only for a `Vis` whose data was collected through Lux's SQL executor. SQL details are owned by `sql-backend`.

Expected export shapes in Lux 0.5.1:

- `to_altair(...)` returns editable Python code as a string. For common marks, it wraps chart code in a helper such as `plot_barchart(...)`, `plot_scatterplot(...)`, `plot_linechart(...)`, or `plot_heatmap(...)`.
- `to_matplotlib()` returns editable Matplotlib Python code as a string and ends with `fig`.
- `to_vegalite(prettyOutput=True)` returns a human-readable string with a copy/edit preamble and formatted JSON.
- `to_vegalite(prettyOutput=False)` returns a Python dictionary. The dictionary contains `vislib: "vegalite"` and usually contains serialized chart `datasets`, making it the safest portable embedded-data artifact.
- `to_code(language="python")` returns data-preparation Python code with a `create_chart_data(ldf, vis)` function for the selected `Vis`.

## 6. Standalone and embedded data

For standalone Altair export, call:

```python
standalone_code = Vis(["normal", "score"], source).to_altair(standalone=True)
```

For unaggregated scatterplots, Lux 0.5.1 emits an `alt.Chart(pd.DataFrame(...))` token that embeds the data in the returned code. For aggregated bar/histogram-style charts, the public `Vis.to_altair(...)` wrapper may still include `visData = create_chart_data(source_df, vis)` rather than a fully embedded dataframe. When a truly portable artifact is required, verify that the returned Altair code contains `pd.DataFrame(...)`; otherwise prefer `to_vegalite(prettyOutput=False)` or manually combine `vis.data.to_dict()` with the exported chart logic.

## 7. Special-character and long-label columns

Altair field names cannot contain dots in the same way Pandas column names can. Lux sanitizes dotted column names in exported Altair/Vega-Lite fields while preserving the original title:

```python
special_vis = Vis(["special.char"], source)
code = special_vis.to_altair()
# Field token: specialchar
# Axis title token: special.char
```

Long labels are abbreviated in generated chart titles and axis titles using Lux's global label-length configuration. If the exact full label is required, export the code and edit the title string manually, or route global label settings to `configuration-actions`.

Create a fresh `Vis` for each export format when testing special-character columns. Some renderer paths mutate compiled attribute names during export, so reusing the same `Vis` across multiple special-character export methods can produce misleading follow-up errors.

## 8. Relationship to `df.exported`

In a notebook/widget workflow, selected visualizations from a Lux dataframe widget are exposed through the dataframe's `exported` property.

```python
# One selected chart:
vis = df.exported[0]      # a Vis
print(vis.to_altair())

# Multiple selected charts:
bookmarked = df.exported  # a VisList-like collection
for selected_vis in bookmarked:
    print(selected_vis.to_vegalite())
```

`df.recommendation` is a dictionary of recommendation category names to `VisList` collections. `df.current_vis` contains currently displayed visualizations. Those dataframe-level recommendation concepts are routed to `pandas-intent-recommendations`; this sub-skill owns what to do once a `Vis` or `VisList` has been selected.
