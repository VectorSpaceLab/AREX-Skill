# API reference for `Clause`, `Vis`, and `VisList`

The signatures below were verified against Lux API 0.5.1. Use them as the runtime contract for direct visualization construction and export.

## Imports

```python
import lux
import pandas as pd
from lux.vis.Clause import Clause
from lux.vis.Vis import Vis
from lux.vis.VisList import VisList
```

Create or reload dataframes after importing Lux so Pandas uses Lux's dataframe subclass.

## `Clause`

Verified class/init signature:

```python
Clause(
    description: Union[str, list] = "",
    attribute: Union[str, list] = "",
    value: Union[str, list] = "",
    filter_op: str = "=",
    channel: str = "",
    data_type: str = "",
    data_model: str = "",
    aggregation: Union[str, callable] = "",
    bin_size: int = 0,
    weight: float = 1,
    sort: str = "",
    timescale: str = "",
    exclude: Union[str, list] = "",
)
```

Verified methods:

```python
Clause.get_attr(self)
Clause.set_aggregation(self, aggregation: Union[str, callable])
Clause.to_string(self)
```

Important fields and accepted values:

- `description`: compact shorthand parsed later by Lux. Examples: `"Horsepower"`, `"Origin=USA"`, `"?"`.
- `attribute`: explicit field name, list of alternative field names, or `"?"` wildcard.
- `value`: explicit filter value, list of alternative filter values, or `"?"` wildcard over unique values.
- `filter_op`: one of `=`, `<`, `>`, `<=`, `>=`, `!=` for filter clauses.
- `channel`: requested encoding channel. Lux supports `"x"`, `"y"`, and `"color"` for direct channel control.
- `data_type`: expected semantic data type such as `"nominal"`, `"quantitative"`, or `"temporal"`.
- `data_model`: `"dimension"` or `"measure"`.
- `aggregation`: aggregation name or callable accepted by Pandas aggregation. `None` disables aggregation for already aggregated data.
- `bin_size`: histogram bin count override.
- `weight`: intended importance weight for scoring.
- `sort`: bar-chart sorting hint such as `"ascending"` or `"descending"`.
- `timescale`: temporal granularity hint.
- `exclude`: value or list used to exclude wildcard candidates.

`set_aggregation(...)` also maintains the internal aggregation display name used in generated labels. `to_string()` returns strings such as `"attribute"`, `"attribute=value"`, or `"a|b"` for list-valued attributes.

## `Vis`

Verified class/init signature:

```python
Vis(intent, source=None, title="", score=0.0)
```

Use `Vis` for exactly one visualization. `intent` can be a list of strings and/or `Clause` objects. `source` should be a Lux dataframe or compatible Pandas dataframe created after importing Lux.

Verified methods and properties:

```python
Vis.get_attr_by_attr_name(self, attr_name)
Vis.get_attr_by_channel(self, channel)
Vis.refresh_source(self, ldf)
Vis.set_intent(self, intent: List[Clause]) -> None
Vis.to_altair(self, standalone=False) -> str
Vis.to_matplotlib(self) -> str
Vis.to_vegalite(self, prettyOutput=True) -> Union[dict, str]
Vis.to_code(self, language="vegalite", **kwargs)

vis.data       # processed chart dataframe
vis.code       # last generated code/specification object
vis.mark       # inferred mark: bar, histogram, scatter, line, heatmap, geographical
vis.min_max    # min/max metadata for relevant quantitative attributes
vis.intent     # original user intent; assigning calls set_intent
```

### `Vis.refresh_source(ldf)`

Recompiles the visualization against a new source dataframe. It parses the original intent, validates it against the new dataframe, compiles channels/marks, and executes the dataframe operation needed to populate `vis.data`. Use this after filtering or replacing the dataframe.

### `Vis.set_intent(intent)`

Updates the original intent and refreshes against the current source. The property assignment `vis.intent = [...]` calls the same method.

### `Vis.to_altair(standalone=False)`

Returns editable Altair Python code as a string. In Lux 0.5.1 the public method emits a helper function name matching the mark where possible, for example `plot_scatterplot`, `plot_barchart`, `plot_linechart`, or `plot_heatmap`.

`standalone=True` requests embedded dataframe code. Verify the returned code: unaggregated scatterplots can include `alt.Chart(pd.DataFrame(...))`, while aggregated charts may still call `create_chart_data(source_df, vis)`. If complete embedded data is required, also consider `to_vegalite(prettyOutput=False)`.

### `Vis.to_matplotlib()`

Returns editable Matplotlib Python code as a string. It includes imports, default style setup, chart-specific data construction, and ends with `fig` so the figure displays in a notebook. In headless scripts, set a noninteractive Matplotlib backend before importing plotting code.

### `Vis.to_vegalite(prettyOutput=True)`

With `prettyOutput=True`, returns a formatted string containing a copy/edit preamble and the Vega-Lite JSON text. With `prettyOutput=False`, returns a Python dictionary. The dictionary contains `vislib: "vegalite"`; for ordinary Pandas-backed charts it also contains the serialized `datasets` payload generated by Altair.

### `Vis.to_code(language=...)`

Supported language values in Lux 0.5.1:

- `"vegalite"`: dispatches to `to_vegalite(...)`.
- `"altair"`: dispatches to `to_altair(...)`.
- `"matplotlib"`: dispatches to `to_matplotlib()`.
- `"matplotlib_svg"`: returns a Matplotlib SVG-oriented object used by Lux internals.
- `"python"`: traces the Pandas executor and returns a `create_chart_data(ldf, vis)` function as code.
- `"SQL"`: returns a SQL query only when the `Vis` was collected through Lux's SQL executor; otherwise it warns.

Unsupported language names produce a warning rather than a useful export. Language matching is case-sensitive for `"SQL"`.

## `VisList`

Verified class/init signature:

```python
VisList(input_lst: Union[List[Vis], List[Clause]], source=None)
```

`input_lst` can be either a list of `Vis` objects or a list of `Clause`/intent units that compile into a collection. For string intent units, Lux parses them into clauses during refresh.

Verified methods and properties:

```python
VisList.get(self, field_name)
VisList.map(self, function)
VisList.normalize_score(self, invert_order=False)
VisList.refresh_source(self, ldf)
VisList.set(self, field_name, field_val)
VisList.set_intent(self, intent: List[Clause]) -> None
VisList.showK(self)
VisList.sort(self, remove_invalid=True, descending=True)

vislist.intent       # original collection intent
vislist.exported     # selected widget visualizations, only when a widget is attached
len(vislist)
vislist[index]
vislist[index] = vis
for vis in vislist: ...
```

### `VisList.refresh_source(ldf)`

Recompiles every visualization in the collection against a new source dataframe. For a clause-based collection, it expands wildcards, validates the intent, compiles visualizations, and executes each visualization. For a list of `Vis` objects, it recompiles each `Vis` with the new source.

### `VisList.sort(remove_invalid=True, descending=True)`

Sorts the collection in place by `Vis.score`. If `remove_invalid=True`, it drops visualizations whose score is `-1`. Global `lux.config.sort` can override the requested direction: `"ascending"`, `"descending"`, or `"none"`.

### `VisList.showK()`

Uses `lux.config.topk`. If top-k is an integer, returns a new `VisList` containing the first `abs(topk)` items. If top-k is `False`, returns the current object. Top-k configuration is a global setting; route global tuning to `configuration-actions`.

### `VisList.normalize_score(invert_order=False)`

Divides each score by the maximum score in the collection. With `invert_order=True`, stores `1 - normalized_score`. Ensure the collection is nonempty and the maximum score is not zero.

### `VisList.map(function)` and `VisList.get(field_name)`

`map` returns Python's lazy `map` object over the collection. Wrap it with `list(...)` when you need materialized results.

`get(field_name)` is shorthand for mapping `getattr(vis, field_name)` over every `Vis`.

```python
marks = list(vislist.get("mark"))
scores = list(vislist.get("score"))
custom = list(vislist.map(lambda v: (v.mark, v.score)))
```

### `VisList.set(field_name, field_val)`

The method exists in Lux 0.5.1 but returns `NotImplemented`. Do not rely on it to mutate a collection. Use an explicit loop instead.

### `VisList.exported`

`VisList.exported` reads selected visualizations from an attached notebook widget. If no widget is attached or no visualization is selected, it warns and returns an empty list. For non-widget scripts, construct `VisList` directly rather than relying on `exported`.
