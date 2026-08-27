# Dataset comparison API reference

Verified package identity for this skill: distribution/import name `sweetviz`, version `2.3.3`. The package has no console entry points; comparison workflows use the Python API.

## Public comparison constructors

| API | Verified signature | Use |
| --- | --- | --- |
| `sweetviz.compare` | `compare(source, compare, target_feat=None, feat_cfg=None, pairwise_analysis='auto')` | Compare two DataFrames such as train/test or baseline/current. |
| `sweetviz.compare_intra` | `compare_intra(source_df, condition_series, names, target_feat=None, feat_cfg=None, pairwise_analysis='auto')` | Split one DataFrame by a boolean Series and compare true vs false groups. |

Do not pass `verbosity` to either public constructor. Verbosity is handled by `DataframeReport.__init__` and Sweetviz configuration defaults, not by `compare()` or `compare_intra()`.

Both constructors return a `DataframeReport`, which can later be saved with `show_html(filepath='SWEETVIZ_REPORT.html', open_browser=True, layout='widescreen', scale=None)`. Use `open_browser=False` for automated agents.

## Accepted input shapes and names

### `compare(source, compare, ...)`

`source` and `compare` each accept either:

- a pandas DataFrame; or
- a two-item list/tuple containing the DataFrame and a display name, e.g. `[train_df, "Training Data"]` or `(test_df, "Test Data")`.

If a bare DataFrame is used, Sweetviz assigns generic display names. Prefer explicit names so report summaries and legends are unambiguous.

### `compare_intra(source_df, condition_series, names, ...)`

- `source_df`: pandas DataFrame to split.
- `condition_series`: pandas Series with the same length as `source_df` and plain boolean dtype.
- `names`: two display names, where `names[0]` labels rows where the condition is true and `names[1]` labels rows where the condition is false.

Validation performed by Sweetviz:

| Check | Failure |
| --- | --- |
| Length of `condition_series` equals length of `source_df` | `ValueError` stating source and condition must be the same length |
| `condition_series` dtype is boolean | `ValueError` stating the condition must be boolean |
| False group is non-empty | `ValueError` stating the false dataset is empty |
| True group is non-empty | `ValueError` stating the true dataset is empty |

Integer `0/1` flags are not accepted directly. Convert them to a plain boolean Series only after verifying they contain no missing values and no values outside `{0, 1}`.

## Target feature interactions

`target_feat` is optional. When provided:

- The target name must exist in the source DataFrame.
- The target cannot be listed in `FeatureConfig(skip=...)`.
- The target must be numeric or boolean for supported target analysis.
- The source target must not contain missing values.
- If the compare DataFrame also has the target column, that compare target must not contain missing values.
- If the compare DataFrame lacks the target column, Sweetviz can still construct a report, but compare-side target overlays are not available; for a true labeled train/test comparison, keep the target in both DataFrames.

Boolean-like target values are sanitized internally for association/target calculations after the target type is determined. Low-cardinality integer features can infer as categorical by default, so coordinate with the configuration-and-data-handling sub-skill when target or feature type intent matters.

## FeatureConfig interactions in comparisons

`FeatureConfig(skip=None, force_cat=None, force_text=None, force_num=None)` accepts strings, lists, or tuples. A single string is normalized to a one-element list. A feature literally named `index` is normalized to `df_index` because Sweetviz renames `index` columns internally.

Important comparison constraints:

- Any feature name mentioned in `FeatureConfig` is case-sensitive.
- Mentioned feature names are checked against the source DataFrame. Avoid placing compare-only columns in `FeatureConfig`.
- Skipped columns are excluded from processed feature details.
- A target cannot be skipped.
- Use `force_num`, `force_cat`, or `force_text` when type inference would otherwise choose a misleading type. Numeric columns with up to the configured distinct-value threshold default to categorical unless forced or configured otherwise.

Detailed type forcing, config overrides, and data cleanup are owned by the configuration-and-data-handling sub-skill.

## Duplicate columns, mixed types, and schema mismatches

- Duplicate columns in source raise `ValueError` and are unsupported.
- Duplicate columns in compare raise `ValueError` and are unsupported.
- Mixed inferred types inside a column are unsupported and raise `TypeError` with remediation guidance.
- Compare feature processing is source-column driven:
  - source columns missing from compare are analyzed as source-only features;
  - compare-only columns are counted in the compare summary as `num_cmp_not_in_source`;
  - compare-only columns do not receive full source-driven feature detail pages.

For strict train/test drift reports, align schemas and dtypes before comparison unless the mismatch itself is the finding being reported.

## Pairwise analysis

Allowed `pairwise_analysis` values are:

| Value | Behavior |
| --- | --- |
| `"off"` | Skip associations and association graphs; preferred for deterministic smoke tests and wide data. |
| `"auto"` | Run associations for small feature counts, but warn and return early above the configured association threshold. |
| `"on"` | Force association computation even when it may be expensive. |

The installed default association auto threshold is 200 features. If `"auto"` returns early on a wide table, rerun with `"off"` for a completed non-association report or `"on"` when the user explicitly wants the expensive associations.

## Rendering and output validation

Comparison constructors only build the `DataframeReport`; they do not write files. To save HTML:

```python
report.show_html("comparison.html", open_browser=False, layout="vertical", scale=0.8)
```

Validate automated output by checking:

1. The expected file exists.
2. The file size is greater than zero.
3. The HTML contains expected dataset labels when practical.

Browser behavior, notebook embedding, layout choice, scaling, and optional Comet.ml logging details are covered by the report-generation sub-skill.
