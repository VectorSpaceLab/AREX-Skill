# Sweetviz data/config troubleshooting

Use these fixes before constructing a Sweetviz report. Rendering problems after a valid report object is created route to `../report-generation/`.

## Duplicate column names

Typical error:

```text
Duplicate column names detected in "source"; this is not supported.
Duplicate column names detected in "compare"; this is not supported.
```

Why it happens: Sweetviz iterates dataframe columns by name and does not support duplicate labels.

Fixes:

```python
# Find duplicates.
duplicates = df.columns[df.columns.duplicated()].tolist()

# Rename deterministically before calling Sweetviz.
seen = {}
new_columns = []
for col in df.columns:
    count = seen.get(col, 0)
    seen[col] = count + 1
    new_columns.append(col if count == 0 else f"{col}_{count}")
df = df.copy()
df.columns = new_columns
```

CSV note: pandas may mangle duplicates during `read_csv`, so use the bundled preflight helper to inspect the raw header before pandas renames anything.

Reserved-name note: a real column named `index` is renamed to `df_index` inside Sweetviz. Avoid having both `index` and `df_index` in the same dataframe, because the internal rename can create ambiguous names.

## Mixed inferred type column

Typical error includes:

```text
Column [...] has a 'mixed' inferred_type ... not currently supported
```

Why it happens: a single column contains values that pandas infers as incompatible families, such as numbers mixed with strings or objects.

Fix by choosing one representation before Sweetviz:

```python
# If the values should be numeric, coerce and then decide how to handle NaN.
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
# Then impute, drop, or leave non-target NaNs according to the analysis plan.

# If the values are identifiers or labels, make them strings.
df["code"] = df["code"].astype("string")
```

Do not rely on `force_num` to parse arbitrary string data. `FeatureConfig` type forcing is limited and works best after pandas dtypes are already clean.

## Wrong inferred type

### Low-cardinality numeric column becomes categorical

By default, numeric columns with at most 10 non-null distinct values infer as categorical. This surprises users with small fixtures, ratings, binned scores, or binary-looking numeric targets.

Fix options:

```python
feat_cfg = sv.FeatureConfig(force_num=["score", "age"])
report = sv.analyze(df, target_feat="target", feat_cfg=feat_cfg, pairwise_analysis="off")
```

or lower the threshold globally in an override file loaded before report construction:

```ini
[Type_Detection]
max_numeric_distinct_to_be_categorical = 2
```

### Numeric-like IDs should be categorical

Use `force_cat` for zip codes, product codes, account buckets, or any number whose magnitude is not meaningful:

```python
feat_cfg = sv.FeatureConfig(force_cat=["zip_code", "product_code"])
```

### High-cardinality text forced categorical

`force_cat` can group high-cardinality text, but the output may become heavy or less useful. Prefer `force_text` for freeform notes, comments, URLs, long labels, or values where top-category grouping hides too much detail.

```python
feat_cfg = sv.FeatureConfig(force_text=["comment", "url"])
```

## Target errors

### Target missing

Typical error:

```text
Feature 'target' was specified as TARGET, but is NOT FOUND in the dataframe
```

Check spelling and case, and remember that a real column named `index` is normalized to `df_index`.

### Target skipped

Typical error:

```text
"target" was also specified as "skip". Target cannot be skipped.
```

Remove the target from `skip`, or choose a different target.

### Target has missing values

Typical errors mention target `NaN (missing) values` in source or compared data.

Sweetviz requires target values to be complete so target distributions and associations are interpretable. Fix before report construction:

```python
# Option A: remove rows missing target.
df = df[df["target"].notna()].copy()

# Option B: impute only when it is statistically valid for your task.
df["target"] = df["target"].fillna(0)
```

If comparing two dataframes, also check the compare dataframe when it contains the same target column.

### Target inferred categorical or text

Typical error:

```text
TARGET values can only be of NUMERICAL or BOOLEAN type for now.
```

Common causes:

- A numeric target has 10 or fewer distinct values and is inferred as categorical.
- A target is encoded as strings like labels or mixed objects.
- `FeatureConfig(force_cat=...)` accidentally includes the target.

Fix numeric targets with `force_num` or pandas dtype cleanup:

```python
feat_cfg = sv.FeatureConfig(force_num="target")
report = sv.analyze(df, target_feat="target", feat_cfg=feat_cfg, pairwise_analysis="off")
```

For binary string labels, either keep them as recognized boolean pairs (`yes`/`no`, `true`/`false`, `y`/`n`, `t`/`f`) or map them explicitly to booleans.

## Missing `FeatureConfig` columns

Typical error:

```text
"feature" was specified in "feature_config" but is not found in source dataframe
```

Sweetviz checks configured feature names against source columns after reserved-name normalization. Confirm case-sensitive spelling and build `FeatureConfig` after any dataframe renaming.

```python
available = set(df.columns).union({"df_index"} if "index" in df.columns else set())
missing = set(feat_cfg.get_all_mentioned_features()) - available
```

## Invalid `compare_intra()` condition

Typical errors:

```text
compare_intra() requires condition_series to be boolean length
compare_intra(): TRUE dataset is empty, nothing to compare!
compare_intra(): FALSE dataset is empty, nothing to compare!
```

Fix by creating an actual boolean Series with both groups populated:

```python
condition = df["segment"].eq("A")
assert condition.dtype == bool
assert condition.any() and (~condition).any()
```

Integer 0/1, `yes`/`no`, and `true`/`false` CSV columns are often condition-like but not guaranteed to be pandas bool dtype. Convert explicitly before calling `compare_intra()`.

## Invalid layout or verbosity

### Layout

Rendering accepts only `widescreen` or `vertical` for HTML and notebook layouts. If a config override or render call uses another value, Sweetviz raises a layout `ValueError`.

```ini
[Output_Defaults]
html_layout = vertical
notebook_layout = vertical
```

### Verbosity

Do not call public constructors as `sv.analyze(..., verbosity="off")` or `sv.compare(..., verbosity="off")` in Sweetviz 2.3.3. The installed public constructors do not accept that keyword.

Use an override instead:

```ini
[General]
default_verbosity = off
```

Then load it before constructing a report:

```python
sv.config_parser.read("sweetviz_override.ini")
report = sv.analyze(df, target_feat="target", feat_cfg=feat_cfg, pairwise_analysis="off")
```

Advanced users can instantiate `sv.DataframeReport(..., verbosity="off")`, but that bypasses the simpler public constructor path and should be chosen intentionally.

## Package assets and fonts

Symptoms:

- Matplotlib glyph warnings for CJK characters.
- Missing template/style/font errors during report generation.
- Reports render but non-Latin plot labels show blank boxes.

Fixes:

- Set CJK support in config before constructing reports:

```ini
[General]
use_cjk_font = 1
```

- Confirm the installed package includes its runtime templates, matplotlib styles, default INI, and fonts. If assets are missing, reinstall the package rather than copying files from a checkout.
- Keep optional Comet.ml credential/service problems separate from local font or asset problems; route Comet upload troubleshooting to `../report-generation/`.

## Preflight with bundled helper

The CSV helper performs safe checks without importing Sweetviz or generating reports:

```bash
python scripts/validate_sweetviz_inputs.py \
  --source-csv data.csv \
  --compare-csv holdout.csv \
  --target survived \
  --skip passenger_id \
  --force-num age \
  --condition-column is_train_group
```

It exits with status 1 when blocking errors are found and prints actionable messages for duplicate columns, missing configured features, skipped targets, target missing values, non-numeric/non-boolean targets, mixed-type hints, and non-boolean or one-sided condition columns.
