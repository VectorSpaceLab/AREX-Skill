# Pandas intent troubleshooting

Use this guide when Lux dataframe recommendations, intent, or Pandas integration do not behave as expected.

## `df.intent` or `df.recommendation` is missing

Likely cause: the object is a plain Pandas dataframe created before Lux was imported.

Fix:

```python
import lux
import pandas as pd

# Recreate/wrap the old object after Lux has been imported.
df = pd.DataFrame(df)
print(type(df))
```

Expected class: `lux.core.frame.LuxDataFrame`. For a column slice, expected class is `lux.core.series.LuxSeries`.

If a library rejects Lux subclasses, pass a plain Pandas object to that library with `df.to_pandas()` and rebuild a Lux dataframe afterward if you need recommendations again.

## `TypeError: Input intent must be either a list ...`

Likely cause: assigning a bare string to `df.intent`.

Wrong:

```python
df.intent = "sales"
```

Right:

```python
df.intent = ["sales"]
df.set_intent(["sales"])
```

## Warning: input attribute does not exist

Likely causes:

- Column name typo.
- Case or whitespace mismatch.
- The intended value was supplied as if it were a column name.

Fix:

```python
print(list(df.columns))
df.intent = ["exact_column_name"]
```

If Lux says a token looks like a value belonging to a particular attribute, use full filter syntax:

```python
# Instead of this:
df.intent = ["West"]

# Use this:
df.intent = ["region=West"]
```

## Warning: input value does not exist for the attribute

Likely causes:

- Filter value is misspelled or differently capitalized.
- The column contains numbers/dates but the filter value was expressed as an incompatible string.
- The dataframe was filtered or mutated after earlier intent examples were written.

Fix:

```python
print(df["region"].unique())
df.intent = ["region=West"]
```

For advanced filter operators or typed values, use `lux.Clause` and route detailed visualization/Clause work to `visualization-export`.

## Recommendations are empty or unexpectedly small

Check these conditions:

1. **Too few rows** — Lux generally needs at least five non-aggregated rows for dataframe recommendations.
2. **Empty dataframe** — Lux cannot visualize an empty dataframe.
3. **Identifier-like columns** — ID columns are suppressed from recommendations.
4. **Ambiguous data types** — wrong semantic types can hide useful tabs; route data-type fixes to `special-data-types`.
5. **Hierarchical indexes** — Lux does not visualize hierarchical index dataframes; use `reset_index()` and route details to `special-data-types`.
6. **Only one useful measure/dimension** — some tabs require at least two quantitative fields or at least one categorical field.

Refresh caches after mutation:

```python
df.expire_metadata()
df.expire_recs()
recs = df.recommendation
```

## Default tabs are missing

Default recommendation tabs are data-dependent. For example:

- No `Correlation` tab if fewer than two quantitative attributes are usable.
- No `Occurrence` tab if no nominal attributes are usable.
- No `Temporal` tab if no temporal fields are inferred.
- No `Distribution` tab if quantitative attributes are unavailable or treated as IDs.

If the field classification looks wrong, use `special-data-types`.

## Intent-specific tabs are missing

Likely causes:

- The intent failed validation and `df.current_vis` is empty.
- The intent compiles to multiple visualizations because of `|`, Python-list OR input, or wildcard `?`.
- The current visualization is not a single supported `Vis` for next-step actions.

Check:

```python
print(df.intent)
print(df.current_vis)
print(df.recommendation.keys())
```

If the intent legitimately represents multiple charts, use `visualization-export` to work with `VisList` directly.

## `df.current_vis` is empty

Likely causes:

- Invalid attribute or filter value.
- Duplicate attributes or unsupported intent combinations.
- A grouped/aggregated result copied an intent that is no longer valid for the new columns.

Fix:

```python
df.clear_intent()
df.intent = ["known_column"]
```

For grouped results, inspect `df.columns` after aggregation and set a new intent that matches the aggregated schema.

## `df.exported` warns and returns `[]`

Expected in non-widget contexts. `df.exported` reads selected visualization state from a Lux widget.

- If no widget has been attached, Lux warns: no widget attached to the dataframe.
- If no visualization was selected in the widget, Lux warns: no visualization selected to export.

For scripts, use:

```python
current = df.current_vis
recs = df.recommendation
```

For chart code export and selected-widget export workflows, use `visualization-export`.

## `save_as_html` fails or produces an incomplete widget

Likely causes:

- Widget frontend packages are missing or disabled.
- The dataframe has no widget state yet and recommendation rendering failed.
- The environment is a non-notebook runtime with limited widget support.

Fixes:

1. Confirm ordinary recommendations work with `df.recommendation`.
2. In a notebook, display `df` once before `save_as_html(...)`.
3. Check Lux widget setup and display configuration using `configuration-actions`.

## `head()` or `tail()` visualizes the previous dataframe

This is expected. Lux intentionally visualizes the pre-`head` or pre-`tail` dataframe and emits a message explaining that behavior, because visualizing only a tiny preview would often be misleading.

If the user needs recommendations for the truncated data itself, explicitly materialize a new Lux dataframe after choosing the sample:

```python
small = pd.DataFrame(df.head(20).to_pandas())
small.expire_metadata()
small.expire_recs()
```

## Grouped data shows `Row Groups` or `Column Groups`

This is expected for pre-aggregated/grouped results. Lux tracks groupby history and treats aggregate outputs differently from raw dataframes. For grouped/indexed display caveats, use `special-data-types`.

If groupby history is not desired:

```python
grouped = df.groupby("region", history=False)
```

## Stale recommendations after dataframe or config changes

For dataframe data/schema changes:

```python
df.expire_metadata()
df.expire_recs()
```

For display/config/action changes, usually only recommendations need refreshing:

```python
df.expire_recs()
```

Route `lux.config` and custom action behavior to `configuration-actions`.
