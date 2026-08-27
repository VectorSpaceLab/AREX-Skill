# Troubleshooting Lux data types and grouped dataframes

Use this guide when Lux's semantic metadata, warnings, or recommendation tabs do not match the user's expectations.

## `df.data_type` is missing, empty, or not Lux-aware

**Likely causes**

- The dataframe was created before `import lux` patched Pandas.
- Metadata has not been recomputed after dataframe mutation.
- The object is a plain Pandas dataframe rather than a Lux dataframe.

**Fixes**

```python
import lux
import pandas as pd

df = pd.DataFrame(...)
print(type(df))          # should be a LuxDataFrame subclass after import lux
print(df.data_type)      # triggers metadata computation when needed
```

After substantial mutation, ask Lux to recompute:

```python
df.expire_metadata()
df.expire_recs()
print(df.data_type)
```

If the object came from external code that created a plain Pandas dataframe before Lux was imported, recreate or copy it after importing Lux.

## A date column is inferred as temporal but Lux warns about conversion

**Symptom**

Lux warns that an attribute may be temporal and suggests a `pd.to_datetime` starter template.

**Cause**

Lux detected date-like strings, numbers, or names, but the Pandas dtype is not datetime64. Lux can infer the semantic type, yet date visualizations are safer after explicit conversion.

**Fix**

```python
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
df.expire_metadata()
df.expire_recs()
```

If the column is not actually temporal, override it instead:

```python
df.set_data_type({"date": "nominal"})       # labels such as release cycle names
df.set_data_type({"Year": "quantitative"})  # numeric measurement named Year
```

If a visualization was created before conversion, recreate it or call `vis.refresh_source(df)`.

## Period values behave differently from datetime64 values

**Symptom**

A monthly/yearly Period column is typed as temporal but warnings or formatting surprises remain.

**Fixes**

- Convert to datetime64 for the most conventional Lux temporal behavior.
- Use Period dtype only when period-granularity labels are important.
- Use the period's string form in filters, such as `"month=2020-03"`.
- Refresh any existing `Vis` after changing the source column.

```python
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
df["month"] = pd.DatetimeIndex(df["date"]).to_period(freq="M")
```

## Geographic recommendations are missing

**Likely causes**

- The location column is not named exactly `state` or `country`.
- The dataframe was created before importing Lux.
- The values are not recognizable state/country names, abbreviations, or codes.
- The user tried `df.set_data_type({"col": "geographical"})`, which is not accepted by the dataframe override API in Lux 0.5.1.

**Fixes**

```python
df = df.rename(columns={"Country Name": "country", "State Code": "state"})
print(df.data_type)
```

Use `state` for US states and `country` for world countries. Keep values in conventional full-name, abbreviation, or code formats. If the next task is building a custom map/chart despite missing automatic recommendations, route to `visualization-export`.

## Numeric categories are plotted as quantitative measures

**Symptom**

A code column appears in histograms or quantitative charts, but it represents categories.

**Fix**

```python
df.set_data_type({"state_code": "nominal"})
df.set_data_type({"rating_bucket": "nominal"})
```

If the codes are identifiers and should not be visualized, use `"id"` instead.

## An ID-like column is not visualized

**Symptom**

Lux reports that a field is not visualized because it resembles an ID field.

**Cause**

The field has high cardinality, unique or evenly spaced values, or `id` in the name. Lux suppresses it to avoid unhelpful identifier charts.

**Fixes**

- Keep true IDs as `id` and do not expect automatic charts for them.
- Override meaningful repeated codes to nominal:

  ```python
  df.set_data_type({"store_id": "nominal"})
  ```

- Override ordered measurements to quantitative:

  ```python
  df.set_data_type({"sequence_num": "quantitative"})
  ```

Then inspect `df.data_type` and regenerate recommendations.

## `set_data_type` raises `ValueError`

**Cause**

The override value is not one of Lux's accepted dataframe-level values.

**Accepted values**

```python
"nominal", "quantitative", "id", "temporal"
```

**Fix**

Check spelling and case. Use `"nominal"`, not `"categorical"`; use `"quantitative"`, not `"numeric"`; use column renaming for geographic inference rather than `"geographical"` overrides.

## Recommendations are stale after a type or dtype change

**Symptoms**

- `df.data_type` looks corrected, but recommendations still reflect old metadata.
- A `Vis` still uses the old mark after a date conversion.

**Fixes**

```python
df.expire_metadata()
df.expire_recs()
_ = df.recommendation
```

For an existing `Vis`:

```python
vis.refresh_source(df)
```

If the chart/export task is now about `Vis`, `VisList`, or code output, route to `visualization-export`.

## `Row Groups` or `Column Groups` are missing

**Likely causes**

- The dataframe is not recognized as pre-aggregated.
- The row index or column index has no useful `name`.
- The operation produced a flat ordinary dataframe rather than a named-index summary.
- The dataframe has a hierarchical index, which Lux does not support.

**Fixes**

```python
summary = df.groupby("category").mean(numeric_only=True)
summary.index.name = "category"
summary.expire_metadata()
summary.expire_recs()
print(summary.recommendation.keys())
```

For pivots/crosstabs, keep row and column indexes named when you want Row/Column Group recommendations. For ordinary intent/recommendation behavior on the original dataframe, route to `pandas-intent-recommendations`.

## Hierarchical-index unsupported message

**Symptom**

Lux says it does not currently support visualizations in a dataframe with hierarchical indexes and asks for a flat table.

**Fix**

```python
flat = hierarchical_df.reset_index()
```

Avoid crosstabs with more than two factors when the result creates MultiIndex rows or columns. If the hierarchy is analytically important, flatten it into explicit columns first and then set or inspect data types on those columns.

## Empty or very small dataframe messages

**Symptoms**

- Empty dataframe: Lux cannot operate on it.
- Fewer than five rows: Lux says the dataframe is too small to visualize.

**Fixes**

- Use at least five rows for ordinary Lux recommendation examples.
- For real analyses, inspect upstream filters or joins that may have removed rows.
- For pre-aggregated summaries, ensure the index is named and the result is recognized as grouped output.

Small dataframes can still be used to inspect `df.data_type`, but they are not reliable for judging automatic recommendation tabs.

## Decision checklist

1. Confirm the object was created after `import lux`.
2. Print `df.data_type` and identify which semantic type is wrong or surprising.
3. Convert real temporal data with `pd.to_datetime`; use Period dtype only when period labels are required.
4. Rename geographic columns to `state` or `country`.
5. Use `set_data_type` for nominal/quantitative/id/temporal overrides.
6. Flatten hierarchical indexes with `reset_index`.
7. Expire metadata/recommendations or refresh existing visualizations after changes.
