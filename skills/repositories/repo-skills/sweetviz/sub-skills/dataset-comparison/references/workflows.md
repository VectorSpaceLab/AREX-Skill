# Sweetviz dataset comparison workflows

These workflows assume `sweetviz` and `pandas` are importable and the input objects are pandas DataFrames. They are designed for automated agents: no browser opening, explicit output paths, and small deterministic examples.

## Shared preflight checklist

Before calling Sweetviz comparison APIs:

- Confirm both DataFrames have unique column names.
- Decide whether this is a two-DataFrame comparison (`compare`) or a one-DataFrame subgroup split (`compare_intra`).
- Use explicit names with two-item lists or tuples, for example `[train_df, "Training Data"]` and `[test_df, "Test Data"]`.
- If using `target_feat`, verify the target column exists in the source DataFrame, is not listed in `FeatureConfig(skip=...)`, is boolean or numeric, and has no missing values. If the compare DataFrame contains the same target column, it must also have no missing values.
- Keep `pairwise_analysis="off"` for smoke tests and wide data unless association graphs are required.
- Render with `open_browser=False` and check that the HTML file exists and has a non-zero size.

To quiet progress output without inventing unsupported constructor parameters, set configuration defaults before constructing the report:

```python
import sweetviz as sv
sv.config_parser["General"]["default_verbosity"] = "off"
```

Do not pass `verbosity=` to `sweetviz.compare()` or `sweetviz.compare_intra()`.

## Compare train and test DataFrames

Tiny schema used by the bundled smoke helper:

| Column | Meaning | Notes |
| --- | --- | --- |
| `id` | row identifier | usually skipped |
| `age` | numeric feature | force numeric if low cardinality would be misleading |
| `fare` | numeric feature | force numeric in tiny examples |
| `segment` | categorical/string feature | shared between source and compare |
| `purchased` | boolean target | no missing values |
| compare-only field | column present only in compare | counted in compare summary, not analyzed as a source feature |

Recipe:

```python
from pathlib import Path
import pandas as pd
import sweetviz as sv

sv.config_parser["General"]["default_verbosity"] = "off"

train_df = pd.DataFrame({
    "id": [101, 102, 103, 104, 105, 106],
    "age": [22.0, 35.0, 41.0, 28.0, 52.0, 46.0],
    "fare": [7.2, 9.5, 11.1, 8.8, 13.0, 12.4],
    "segment": ["A", "B", "A", "B", "A", "B"],
    "purchased": [True, False, False, True, True, False],
})

test_df = pd.DataFrame({
    "id": [201, 202, 203, 204, 205],
    "age": [24.0, 33.0, 43.0, 31.0, 55.0],
    "fare": [7.4, 10.2, 10.9, 9.1, 14.2],
    "segment": ["A", "B", "B", "A", "B"],
    "purchased": [True, False, False, True, False],
    "campaign_seen": [1, 0, 1, 1, 0],  # compare-only column
})

feature_config = sv.FeatureConfig(skip="id", force_num=["age", "fare"])
report = sv.compare(
    [train_df, "Training Data"],
    [test_df, "Test Data"],
    target_feat="purchased",
    feat_cfg=feature_config,
    pairwise_analysis="off",
)

# User-level check for compare-only columns.
assert report.summary_compare["num_cmp_not_in_source"] == 1

output_path = Path("sweetviz_compare_report.html")
report.show_html(str(output_path), open_browser=False, layout="vertical", scale=0.8)
assert output_path.exists() and output_path.stat().st_size > 0
```

### Column mismatch behavior

Sweetviz builds feature detail pages from source DataFrame columns after skipped columns are removed.

- Columns present in source but missing from compare are still analyzed as source-only features.
- Columns present only in compare are counted in the compare summary as compare-only columns.
- Compare-only columns are not processed as full feature detail pages because the processing loop is source-column driven.
- `FeatureConfig` names are checked against source columns; do not use `FeatureConfig` to refer only to a compare-only column.

For strict drift analysis, align schemas before calling Sweetviz or explicitly document which columns are intentionally source-only or compare-only.

## Compare two subsets of one DataFrame with compare_intra

Use `compare_intra` when both groups come from the same DataFrame and the split can be expressed as a boolean Series.

```python
from pathlib import Path
import pandas as pd
import sweetviz as sv

sv.config_parser["General"]["default_verbosity"] = "off"

df = pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6],
    "age": [21.0, 37.0, 45.0, 29.0, 50.0, 42.0],
    "fare": [7.1, 8.5, 12.0, 9.7, 14.1, 11.6],
    "segment": ["A", "B", "A", "B", "A", "B"],
    "purchased": [True, False, False, True, True, False],
})

condition = df["segment"].eq("A")
assert condition.dtype == bool
assert condition.any() and (~condition).any()

feature_config = sv.FeatureConfig(skip="id", force_num=["age", "fare"])
report = sv.compare_intra(
    df,
    condition,
    ["Segment A", "Not Segment A"],
    target_feat="purchased",
    feat_cfg=feature_config,
    pairwise_analysis="off",
)

output_path = Path("sweetviz_compare_intra_report.html")
report.show_html(str(output_path), open_browser=False, layout="vertical", scale=0.8)
assert output_path.exists() and output_path.stat().st_size > 0
```

### Integer 0/1 conditions are not accepted directly

`compare_intra` checks for a boolean dtype. An integer flag such as `0/1` fails even if it is logically boolean. Convert only after validating the values and missingness:

```python
flag = df["is_segment_a_flag"]
if flag.isna().any() or not set(flag.unique()).issubset({0, 1}):
    raise ValueError("Subgroup flag must contain only non-missing 0/1 values before conversion.")
condition = flag.astype(bool)
assert condition.dtype == bool
assert condition.any() and (~condition).any()
```

For nullable boolean data, fill or drop missing values first and convert to a plain boolean Series before calling `compare_intra`.

## Target-aware comparison choices

- If both train and test contain labels, pass `target_feat="target_column"` and validate missing values in both DataFrames before construction.
- If the compare/test DataFrame does not contain labels, either omit `target_feat` or document that target-aware overlays apply only to the source side.
- If target values are low-cardinality integers and should be interpreted as continuous numeric rather than categorical/boolean, coordinate with the configuration-and-data-handling sub-skill and use a suitable `FeatureConfig` or config threshold.

## Pairwise analysis decisions

- `pairwise_analysis="off"`: fastest and safest for smoke tests, CI-like checks, wide tables, and comparison workflows where association graphs are not needed.
- `pairwise_analysis="auto"`: acceptable for small DataFrames. Above the configured association threshold, Sweetviz warns and returns early instead of completing pairwise analysis.
- `pairwise_analysis="on"`: explicitly asks Sweetviz to compute associations even when it may be expensive.

For wide comparison reports, prefer `"off"` if the user only needs summary and feature distributions.

## Deterministic helper script

Run the bundled helper with an empty output directory:

```bash
python scripts/sweetviz_compare_smoke.py --mode both --output-dir ./sweetviz-compare-smoke --pairwise-analysis off
```

To demonstrate the non-boolean condition failure without rendering an invalid report:

```bash
python scripts/sweetviz_compare_smoke.py --mode compare-intra --invalid-condition-demo --output-dir ./sweetviz-compare-smoke
```
