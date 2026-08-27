# Visualization export troubleshooting

Use this guide after selecting the `visualization-export` sub-skill. It focuses on `Clause`, `Vis`, `VisList`, wildcard enumeration, source refresh, and code/spec export failures.

## `TypeError: intent ... corresponds to more than one visualization`

Cause: `Vis(...)` was used with collection intent. Lux treats `"?"`, alternatives such as `"a|b"`, and list-valued attributes as instructions to enumerate multiple charts.

Fix:

```python
# Wrong for wildcard/multiple charts
# Vis(["normal", "?"], df)

# Right
from lux.vis.VisList import VisList
vislist = VisList(["normal", "?"], df)
```

Then export one visualization at a time:

```python
for vis in vislist:
    print(vis.to_altair())
```

## No data is populated in `Vis`

Cause: the `Vis` was created without a source dataframe, or the source was removed/stale.

Fix:

```python
vis = Vis(["normal", "score"], df)
# or, if the source was missing at construction time:
vis.refresh_source(df)
```

If you filtered or replaced the dataframe, refresh before exporting:

```python
subset = df[df["category"] == "A"]
vis.refresh_source(subset)
```

## Dataframe was created before importing Lux

Cause: Lux monkeypatches Pandas dataframe/series classes at import time. A dataframe created before `import lux` may not have Lux metadata, recommendation, or export behavior.

Fix: import Lux first, then recreate or reload the dataframe.

```python
import lux
import pandas as pd

df = pd.DataFrame(...)
```

## `VisList` has no direct `to_altair`/`to_matplotlib` method

Cause: export methods are defined on individual `Vis` objects, not on the collection.

Fix:

```python
vislist = VisList(["normal", "?"], df)
altair_exports = [vis.to_altair() for vis in vislist]
vegalite_exports = [vis.to_vegalite(prettyOutput=False) for vis in vislist]
```

For a single selected widget chart, use `df.exported[0]`. For multiple selected widget charts, treat `df.exported` as a collection and iterate it.

## `df.exported` or `VisList.exported` is empty

Cause: no notebook widget selection exists, or a `VisList` was constructed in a script without an attached widget.

Fix:

- In a notebook, display the dataframe or `VisList`, select one or more charts in the widget, and use the export button before reading `exported`.
- In scripts or tests, construct `Vis`/`VisList` directly instead of using widget selection state.

## Special-character columns export with renamed fields

Symptom: a column such as `special.char` appears as `specialchar` in Altair/Vega-Lite field tokens, while the axis title remains `special.char`.

Cause: Altair field references cannot safely use dotted Pandas column names. Lux sanitizes the field name for the chart specification.

Fix:

- Treat the sanitized field token as expected in exported Altair/Vega-Lite code.
- If editing the exported code manually, keep the data column and the encoding field names consistent.
- Create a fresh `Vis` for each export format when testing dotted columns; some renderer paths mutate compiled attribute names during export.
- If `to_code("python")` or follow-up export fails after an Altair export on dotted columns, rebuild the `Vis` from the original dataframe and try the export again, or temporarily rename the dataframe columns to export-safe names before constructing the `Vis`.

## Long axis labels or filter titles are abbreviated

Cause: Lux abbreviates long labels in generated chart code. This affects axis titles, chart titles, and long filter descriptions.

Fix:

- Edit the exported code's title/axis strings manually when you need the full label.
- If you want to change global label abbreviation rules, route to `configuration-actions` for `lux.config.label_len` and related plotting configuration.

## `to_altair(standalone=True)` is not fully embedded

Symptom: returned Altair code still contains `create_chart_data(source_df, vis)` instead of only an embedded `pd.DataFrame(...)`.

Cause: in Lux 0.5.1, unaggregated scatterplot standalone output can embed data, but aggregated bar/histogram-style chart helpers can still depend on chart-data creation code.

Fix:

- Inspect the returned code for `pd.DataFrame(...)` before treating it as portable standalone code.
- Use `to_vegalite(prettyOutput=False)` when you need a serialized spec with embedded datasets.
- Or copy `vis.data.to_dict()` into your edited Altair code and point `alt.Chart(...)` to that dataframe.

## Matplotlib export fails or opens windows in automation

Cause: Matplotlib may use an interactive backend in scripts or headless environments.

Fix: set a noninteractive backend before import or execution.

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")
```

Then create the `Vis` and call `to_matplotlib()`.

## Unsupported `to_code(language=...)`

Symptom: Lux warns about an unsupported plotting backend or returns `None`.

Cause: the language value does not match one of Lux 0.5.1's supported strings.

Fix: use one of:

```python
"vegalite", "altair", "matplotlib", "matplotlib_svg", "python", "SQL"
```

`"SQL"` is uppercase and is only useful for SQL-executor visualizations; route SQL workflows to `sql-backend`.

## `VisList.set(...)` does not update values

Cause: `VisList.set(field_name, field_val)` is present but returns `NotImplemented` in Lux 0.5.1.

Fix:

```python
for vis in vislist:
    setattr(vis, "score", 1.0)
```

## `normalize_score()` fails or creates invalid scores

Cause: the collection is empty, or all scores are zero so the maximum score is zero.

Fix:

```python
scores = list(vislist.get("score"))
if scores and max(scores) != 0:
    vislist.normalize_score()
else:
    # assign scores manually or skip normalization
    pass
```

## Exported code contains global styles you did not expect

Cause: `lux.config.plotting_style`, `plotting_backend`, `plotting_scale`, label length, top-k, and sort settings are global and can affect exported code.

Fix: route global plotting/backend/style configuration to `configuration-actions`. For this sub-skill, either use the current configuration as-is or create a fresh process/session with known Lux config before exporting.
