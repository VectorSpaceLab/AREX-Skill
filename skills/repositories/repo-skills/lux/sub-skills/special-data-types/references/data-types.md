# Lux semantic data types, temporal/geographic columns, and index groups

Lux extends Pandas dataframes with semantic metadata that drives recommendation generation. These semantic data types are different from Pandas dtypes: a Pandas integer column can be `quantitative`, `nominal`, `temporal`, or `id` in Lux depending on cardinality, name, content, and context.

Import Lux before creating Pandas objects so dataframes become Lux-enabled:

```python
import lux
import pandas as pd

df = pd.DataFrame(...)
print(df.data_type)
```

Accessing `df.data_type` computes metadata when needed and returns a mapping from column or named index to Lux semantic type.

## Supported semantic types

| Type | Meaning in Lux | Common recommendation effect |
| --- | --- | --- |
| `quantitative` | Numeric measures with meaningful order and magnitude. | Correlation scatterplots/heatmaps and distribution histograms. |
| `nominal` | Unordered categorical attributes, including low-cardinality numeric codes. | Occurrence bars and dimension fields in charts. |
| `geographical` | Location columns recognized by name, especially `state` or `country`. | Geographic choropleth-style recommendations when paired with measures. |
| `temporal` | Dates, times, periods, or date-like attributes. | Temporal line charts and time-scale recommendations. |
| `id` | Identifier-like fields such as record, user, product, or serial IDs. | Suppressed from visualization; Lux warns that the field resembles an ID. |

## Inference rules that matter in practice

Lux's exact inference is heuristic, but these rules are the most actionable:

- A Pandas datetime64 column is temporal.
- A Pandas Period dtype is treated as temporal for Lux metadata.
- Date-like strings or date-like numbers can be inferred as temporal, but Lux warns that you should convert the column to Pandas datetime for accurate visualization.
- Column names such as `month`, `year`, `day`, `date`, `time`, and `weekday` are temporal signals.
- Columns named `state` or `country` are geographic signals; use those exact names when you want geographic detection.
- Low-cardinality numeric or float columns can be nominal even if Pandas stores them as numbers.
- High-cardinality unique/evenly-spaced columns, especially with `id` in the name, can be classified as `id` and suppressed.
- Named non-integer row indexes are added to the data-type mapping as nominal because Lux treats them as operated-on dimensions.

## Overriding an inferred type

Use `df.set_data_type(...)` when Lux's semantic inference is wrong for the user's analysis goal:

```python
# Numeric state codes should be categorical labels, not a numeric measure.
df.set_data_type({"state_code": "nominal"})

# A year-like integer that is actually a measurement can be forced quantitative.
df.set_data_type({"Year": "quantitative"})

# A meaningful code should be visualized as categories instead of suppressed as ID.
df.set_data_type({"product_code": "nominal"})
```

In Lux 0.5.1, `set_data_type` accepts these override values: `"nominal"`, `"quantitative"`, `"id"`, and `"temporal"`. An invalid string raises `ValueError`. Although Lux can infer `geographical`, the dataframe-level override API does not accept `"geographical"`; to fix missing geographic behavior, rename the column to `state` or `country` and use standard values.

`set_data_type` updates the stored metadata and expires cached recommendations. If a visualization object was constructed before the change, reconstruct it or refresh its source according to the visualization workflow.

## Temporal columns

### Convert strings before relying on chart behavior

Lux can detect date-like strings, but it warns because charts are more accurate when the Pandas dtype is datetime-like:

```python
import lux
import pandas as pd

sales = pd.DataFrame({
    "date": ["2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01", "2020-05-01"],
    "value": [10, 15, 20, 25, 22],
})

# Better than leaving date as object strings:
sales["date"] = pd.to_datetime(sales["date"], format="%Y-%m-%d")
print(sales.data_type["date"])  # temporal
```

If a `Vis` was built while the date column was still a string, refresh it after conversion:

```python
from lux.vis.Vis import Vis

vis = Vis(["date", "value"], sales)
sales["date"] = pd.to_datetime(sales["date"], format="%Y-%m-%d")
vis.refresh_source(sales)
```

### Use Period dtype when the label granularity matters

For monthly or yearly display semantics, convert datetime values to a Period dtype:

```python
sales["date"] = pd.to_datetime(sales["date"], format="%Y-%m-%d")
sales["month"] = pd.DatetimeIndex(sales["date"]).to_period(freq="M")
print(sales.data_type["month"])  # temporal
```

Period filters should use the period's string representation, such as `"month=2020-03"`, when specifying an intent. For detailed intent syntax, use the `pandas-intent-recommendations` sub-skill.

## Geographic columns

Lux recognizes geographic attributes by the column name `state` for US states and `country` for world countries. If a dataframe uses names such as `province`, `nation`, `Country Name`, or `state_code`, rename the column before expecting geographic recommendations:

```python
geo_df = geo_df.rename(columns={"Country Name": "country"})
```

Use conventional values:

- `state`: full state names, two-letter abbreviations, or FIPS-style codes.
- `country`: full country names, two/three-letter abbreviations, or ISO-style numeric codes.

If geographic recommendations are still missing, first verify `df.data_type["state"]` or `df.data_type["country"]`. If it is not `geographical`, check the column spelling and whether the dataframe was created after importing Lux.

## ID suppression

Lux intentionally avoids plotting ID-like fields because identifiers usually produce unhelpful charts. The user-facing message is of the form:

```text
<field> is not visualized since it resembles an ID field.
```

If a field is truly only an identifier, keep it as `id` and use it for joins, lookup, or filtering outside Lux's automatic recommendation set. If the field is analytically meaningful, override it:

```python
df.set_data_type({"store_id": "nominal"})      # category labels
df.set_data_type({"sensor_id": "nominal"})     # repeated device categories
df.set_data_type({"sequence_num": "quantitative"})  # ordered measurement
```

## Named indexes, groupby output, pivots, and crosstabs

Lux has special recommendations for pre-aggregated dataframes and named indexes:

- `Row Groups`: visualizations with respect to row-wise index values.
- `Column Groups`: visualizations with respect to column-wise index values.

These appear when Lux recognizes a pre-aggregated dataframe, such as a groupby aggregation, pivot, or crosstab with named row or column indexes.

```python
summary = df.groupby("FundingModel").mean(numeric_only=True)
summary.index.name = "FundingModel"
print(summary.recommendation.keys())
```

For wide time-series or crosstab outputs, give meaningful index names so Lux can treat the row/column labels as dimensions. Lux preserves the row/column order for these group recommendations instead of reranking by interestingness.

### Hierarchical-index limitation

Lux 0.5.1 does not support recommendations for dataframes with multiple row-index levels or multiple column-index levels. Flatten them before visualization:

```python
flat = hierarchical_df.reset_index()
```

Crosstabs with more than two factors commonly produce hierarchical indexes; flatten or simplify them before using Lux.

## Empty and small dataframes

Lux can attach messages instead of recommendations in these cases:

- Empty dataframe: Lux cannot operate on an empty dataframe.
- Fewer than five rows: Lux says the dataframe is too small to visualize unless it is a recognized pre-aggregated structure.
- Hierarchical indexes: Lux asks you to convert to a flat table via `pandas.DataFrame.reset_index`.

When building a minimal example, use at least five rows for ordinary recommendation generation. Smaller fixtures are still useful for checking `df.data_type`, but not for judging Lux's recommendation tabs.
