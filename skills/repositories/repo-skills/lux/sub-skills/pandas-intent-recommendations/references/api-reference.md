# Pandas intent API reference

This reference summarizes Lux 0.5.1 behavior relevant to Pandas-integrated recommendations.

## Import and class identity

```python
import lux
import pandas as pd
from lux.core.frame import LuxDataFrame
from lux.core.series import LuxSeries

assert isinstance(pd.DataFrame({"x": [1, 2, 3, 4, 5]}), LuxDataFrame)
```

Lux import behavior:

- `import lux` registers default recommendation actions and enables Pandas integration.
- New `pd.DataFrame` objects are instances of `lux.core.frame.LuxDataFrame`.
- New `pd.Series` objects and sliced dataframe columns are instances of `lux.core.series.LuxSeries`.
- Common Pandas reader internals are patched so `pd.read_csv`, `pd.read_excel`, `pd.read_json`, and similar loaders return Lux dataframes when they construct new Pandas objects after Lux has been imported.
- Original Pandas classes remain available internally for `to_pandas()` conversion.

## `LuxDataFrame` core methods and properties

Constructor:

```python
LuxDataFrame(*args, **kw)
```

Frequently used methods:

| API | Signature | Notes |
| --- | --- | --- |
| `df.set_intent` | `(intent: list[str | lux.Clause])` | Expires recommendations, parses/validates intent, compiles `current_vis`. |
| `df.clear_intent` | `()` | Sets intent to an empty list and expires recommendations. |
| `df.set_intent_as_vis` | `(vis: lux.vis.Vis)` | Copies a `Vis` object's inferred intent onto the dataframe and recompiles. |
| `df.to_pandas` | `()` | Returns an original Pandas dataframe view/object for code that cannot handle Lux subclasses. |
| `df.save_as_html` | `(filename="export.html", output=False)` | Saves or returns static widget HTML. Requires widget state and widget dependencies. |
| `df.expire_recs` | `()` | Clears cached recommendations, widget, recommendation info, and samples under lazy maintenance. |
| `df.expire_metadata` | `()` | Clears cached type, cardinality, min/max, and structural metadata under lazy maintenance. |
| `df.maintain_metadata` | `()` | Computes metadata when missing or stale. Usually called lazily. |
| `df.maintain_recs` | `(is_series="DataFrame")` | Computes recommendation collections and widget payload. Usually called lazily. |
| `df.head` | `(n=5)` | Returns a Lux dataframe that visualizes the previous dataframe when displayed. |
| `df.tail` | `(n=5)` | Same caveat as `head`. |
| `df.groupby` | `(*args, **kwargs)` | Returns a Lux-aware groupby object; accepts `history=False` to avoid recording groupby history. |

Key properties:

| Property | Type / return | Behavior |
| --- | --- | --- |
| `df.intent` | list of parsed `lux.Clause` objects | Setter accepts a list of strings/clauses or a `Vis`; a bare string is invalid. |
| `df.current_vis` | `VisList` or empty list | Compiled visualization(s) for current intent. Requesting it can execute/attach data to the vis list. |
| `df.recommendation` | `dict[str, VisList]` | Lazy recommendation dictionary keyed by tab/action labels. |
| `df.exported` | `[]`, `VisList`, or `dict[str, VisList]` | Widget-selected visualizations. Without an attached widget or selection it warns and returns `[]`. |
| `df.widget` | Lux widget object or `None` | Set after widget rendering/recommendation maintenance when widget rendering is enabled. |
| `df.history` | Lux history object | Records selected Pandas operations such as `head`, `tail`, and `groupby`. |

## Intent setter details

Valid forms:

```python
df.intent = ["sales"]
df.intent = ["sales", "profit"]
df.intent = ["region=West"]
df.intent = ["region=West|East"]
df.intent = [["sales", "profit"], "region"]
df.intent = [lux.Clause(attribute="sales", channel="x")]
df.intent = some_vis
```

Invalid form:

```python
df.intent = "sales"  # TypeError: input intent must be a list or a Vis object
```

Parsing behavior:

- String attributes become `Clause(attribute="...")`.
- `"attribute=value"` becomes a filter clause with `filter_op="="`.
- `|` inside an attribute or value expression becomes an OR list.
- A Python list inside the intent list also becomes an OR list for attributes.
- `?` is a wildcard/enumeration marker; detailed wildcard collection handling belongs in `visualization-export`.
- `Clause` can express channel, aggregation, data type, data model, bin size, sorting, filter operators, and exclusions.

Validation behavior:

- Missing attributes emit a warning naming the invalid attribute.
- A value supplied without its attribute can emit a warning suggesting `attribute=value` syntax when Lux can match that value to a column.
- Missing filter values emit a warning naming the invalid value and attribute.
- Invalid intent returns an empty `current_vis` rather than useful next-step recommendations.

## Recommendation actions

Default actions are registered when Lux is imported. The returned recommendation dictionary uses display/action labels.

| Condition | Possible recommendation keys |
| --- | --- |
| No compiled current visualization | `Correlation`, `Distribution`, `Occurrence`, `Temporal`, `Geographical` depending on available columns and types. |
| Exactly one current visualization from intent | `Enhance`, `Filter`, `Generalize`; `Similarity` can replace filter-style recommendations for suitable filtered line-chart intents. |
| Multiple current visualizations | Custom/multi-vis behavior may appear; route custom action details to `configuration-actions` and multi-vis handling to `visualization-export`. |

Each dictionary value is a `VisList`. It can be iterated, indexed, and passed to export-oriented helpers described in `visualization-export`.

## `current_vis` and export facts

`df.current_vis` is a `VisList` of compiled visualizations for the dataframe's current intent.

```python
df.intent = ["sales", "profit"]
current = df.current_vis
assert len(current) == 1
vis = current[0]
print(vis.mark)
```

For non-notebook programmatic checks, prefer facts such as:

```python
spec = current[0].to_code(language="vegalite", prettyOutput=False)
assert isinstance(spec, dict)
assert "mark" in spec or "encoding" in spec
```

Detailed export methods and chart editing are owned by `visualization-export`; this sub-skill only establishes that `current_vis` and recommendation entries are exportable Lux visualization objects.

## `exported` return shapes

`df.exported` reads selection state from the attached Lux widget.

| Widget state | Return |
| --- | --- |
| No widget attached | Warns and returns `[]`. |
| Widget attached, no selected visualizations | Warns and returns `[]`, unless a previous selection was saved. |
| Only current visualization selected | Returns `df.current_vis`. |
| One recommendation tab selected | Returns a `VisList` for the selected charts. |
| Multiple tabs selected | Returns a dictionary mapping tab names to `VisList` objects; current-vis selections use the `Current Vis` key. |

## `LuxSeries` essentials

Constructor:

```python
LuxSeries(*args, **kw)
```

Important behavior:

- `series.to_pandas()` returns the original Pandas series object/class.
- `series.recommendation` builds a temporary one-column `LuxDataFrame` to compute recommendations.
- `series.exported` delegates to the dataframe used for Series display, so it is meaningful only after display/widget attachment.
- Mixed-type row-like Series and dtype Series fall back to ordinary Pandas-style display rather than visual recommendations.
- Series `groupby` propagates Lux metadata and marks the result as pre-aggregated.

## Dataframe conversion and cache APIs

Use `to_pandas()` for third-party compatibility:

```python
plain = df.to_pandas()
```

Use cache expiration when recommendations or metadata need recomputation:

```python
df.expire_metadata()
df.expire_recs()
recs = df.recommendation
```

Use `maintain_metadata()` and `maintain_recs()` sparingly; regular property access usually invokes them lazily.
