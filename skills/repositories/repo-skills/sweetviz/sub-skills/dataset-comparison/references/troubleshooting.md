# Dataset comparison troubleshooting

Use this reference for comparison-specific failures. For single-report rendering, browser, notebook, optional Comet.ml, install/import, package-data, or font issues, route to the Sweetviz root or report-generation guidance.

## compare_intra condition is not boolean

**Symptom**

`ValueError: compare_intra() requires condition_series to be boolean length`

**Cause**

The condition is not a plain boolean pandas Series. Common mistakes include integer `0/1` flags, strings such as `"yes"/"no"`, nullable boolean data with missing values, or passing a scalar expression instead of a Series.

**Fix**

Create and validate a boolean Series before calling Sweetviz:

```python
condition = df["segment"].eq("A")
if condition.dtype != bool:
    raise TypeError("condition must be a plain boolean Series")
if not condition.any() or not (~condition).any():
    raise ValueError("both compare_intra groups must be non-empty")
```

For integer flags, first verify no missing values and only `{0, 1}` are present, then convert with `astype(bool)`.

## compare_intra split is empty

**Symptoms**

- `ValueError: compare_intra(): FALSE dataset is empty, nothing to compare!`
- `ValueError: compare_intra(): TRUE dataset is empty, nothing to compare!`

**Cause**

The condition selected all rows or no rows.

**Fix**

Inspect value counts before calling Sweetviz:

```python
counts = condition.value_counts(dropna=False)
if not condition.any() or not (~condition).any():
    raise ValueError(f"condition must create two non-empty groups; got {counts.to_dict()}")
```

If the split is legitimately one-sided, use a single-DataFrame report via report-generation instead of `compare_intra`.

## compare_intra condition length mismatch

**Symptom**

`ValueError: compare_intra() expects source_df and condition_series to be the same length`

**Cause**

The condition Series was created from a different DataFrame, filtered object, or stale index alignment.

**Fix**

Create the condition from the exact DataFrame passed as `source_df`, after final filtering and row selection:

```python
df_for_report = df.loc[mask].copy()
condition = df_for_report["segment"].eq("A")
report = sv.compare_intra(df_for_report, condition, ["A", "not A"], pairwise_analysis="off")
```

## Duplicate columns in source or compare

**Symptoms**

- `ValueError: Duplicate column names detected in "source"; this is not supported.`
- `ValueError: Duplicate column names detected in "compare"; this is not supported.`

**Cause**

Sweetviz does not support duplicate column names.

**Fix**

Rename or drop duplicate columns before comparison. Preserve a mapping outside the report if the original names are important.

## Target contains missing values

**Symptoms**

- `Target feature '<name>' contains NaN (missing) values.`
- `Target feature '<name>' in COMPARED data contains NaN (missing) values.`

**Cause**

Sweetviz requires target features to have no missing values. In compare reports, the source target is always checked; the compare target is also checked when the compare DataFrame contains the target column.

**Fix**

Before constructing the report, choose a policy appropriate to the analysis:

- drop rows with missing target;
- impute target only if statistically justified;
- omit `target_feat` if target analysis is not needed;
- if test labels are unavailable, omit the target from the compare DataFrame or omit `target_feat` and state that the report is not target-aware.

## Target is missing, skipped, or wrong type

**Symptoms**

- `KeyError` stating the target was specified but not found.
- `ValueError` stating the target was also specified as skipped.
- Unexpected categorical behavior for a numeric-looking target.

**Causes and fixes**

- Check exact case-sensitive column spelling in the source DataFrame.
- Remove the target from `FeatureConfig(skip=...)`.
- Ensure the target is boolean or numeric for supported target analysis.
- Numeric columns with low distinct counts can infer as categorical by default. Use configuration-and-data-handling guidance when a low-cardinality numeric target or feature should be forced numeric.

## FeatureConfig name is not found

**Symptom**

`ValueError: "<name>" was specified in "feature_config" but is not found in source dataframe (watch case-sensitivity?).`

**Cause**

FeatureConfig names are validated against the source DataFrame. This includes skipped and forced names. Compare-only columns should not be referenced in `FeatureConfig` unless the schema is aligned so the name also exists in source.

**Fix**

- Correct spelling and case.
- Apply feature forcing only to source columns.
- Align source/compare schemas if the same feature should be configured in both.
- Remember that a literal column named `index` is normalized to `df_index` by Sweetviz/FeatureConfig.

## Mixed inferred types or source/compare type mismatch

**Symptom**

`TypeError` describing a column with mixed inferred type, or a conversion/type mismatch between source and compared DataFrames.

**Cause**

A column contains incompatible Python values, or source and compare versions of the same column infer to incompatible types.

**Fix**

Normalize dtypes before comparison:

```python
df["feature"] = df["feature"].astype(str)          # for categorical/text intent
# or
df["feature"] = pd.to_numeric(df["feature"], errors="coerce")
```

Then handle any new missing values and use `FeatureConfig` only when the data can safely be coerced.

## Pairwise auto threshold warning or incomplete report construction

**Symptom**

Sweetviz prints a pairwise calculation length warning when `pairwise_analysis="auto"` and the number of processed features exceeds the configured threshold.

**Cause**

Associations scale roughly quadratically with feature count. In `auto`, Sweetviz warns and returns early above the threshold.

**Fix**

- Use `pairwise_analysis="off"` to produce a completed report without association graphs.
- Use `pairwise_analysis="on"` only when the user explicitly accepts the runtime cost.
- Reduce columns with `FeatureConfig(skip=...)` or upstream feature selection.

## Compare-only columns are missing from feature details

**Symptom**

A column present only in the compare DataFrame appears in summary counts but not as a full feature page.

**Cause**

Sweetviz processes feature details from source columns. Compare-only columns are counted in the compare summary as compare-only, but are not processed as source-driven feature details.

**Fix**

If compare-only fields need full detail pages, align schemas before comparison or swap source/compare roles for a second report. Document why the schema mismatch exists.

## HTML file is missing or browser behavior is wrong

**Symptom**

The report object is created, but the expected HTML file is not where the user expects or a browser opens unexpectedly.

**Fix**

Call:

```python
report.show_html("comparison.html", open_browser=False)
```

Then validate file existence and size. Route layout, browser, notebook, and optional Comet.ml behavior to the report-generation sub-skill.
