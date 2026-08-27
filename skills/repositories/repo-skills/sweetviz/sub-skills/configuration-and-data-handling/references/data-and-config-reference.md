# Sweetviz data and configuration reference

This reference covers input validation, `FeatureConfig`, type inference, and INI overrides for Sweetviz 2.3.3. Use it before constructing a report or comparison object.

## Public configuration surface

```python
import sweetviz as sv

feat_cfg = sv.FeatureConfig(
    skip=["raw_id", "freeform_blob"],
    force_num="rating",          # keep low-cardinality numeric data numeric
    force_cat=["zip_code"],      # summarize numeric-like identifiers as categories
    force_text=("notes",),       # keep high-cardinality text in text mode
)

# Public constructors do not accept a verbosity argument in Sweetviz 2.3.3.
report = sv.analyze(df, target_feat="target", feat_cfg=feat_cfg, pairwise_analysis="off")
```

Verified public constructor signatures:

- `sweetviz.analyze(source, target_feat=None, feat_cfg=None, pairwise_analysis='auto')`
- `sweetviz.compare(source, compare, target_feat=None, feat_cfg=None, pairwise_analysis='auto')`
- `sweetviz.compare_intra(source_df, condition_series, names, target_feat=None, feat_cfg=None, pairwise_analysis='auto')`
- `sweetviz.FeatureConfig(skip=None, force_cat=None, force_text=None, force_num=None)`

`DataframeReport.__init__` has a `verbosity` parameter, but normal user workflows should prefer public constructors plus `[General] default_verbosity` config overrides unless they intentionally need the lower-level class.

## `FeatureConfig` behavior

`FeatureConfig` controls what Sweetviz does before automatic type detection:

| Argument | Effect | Typical use |
| --- | --- | --- |
| `skip` | Exclude features from analysis. | IDs, raw text dumps, leakage columns, columns known to break analysis. |
| `force_cat` | Treat a feature as categorical. | Numeric identifiers, zip/postal codes, code values, high-cardinality text that must be grouped. |
| `force_text` | Treat a feature as text. | Notes, comments, URLs, freeform strings that should not be grouped. |
| `force_num` | Treat a feature as numeric when compatible. | Low-cardinality numeric columns that Sweetviz would otherwise infer as categorical. |

Normalization details:

- A single string becomes a one-element internal list: `force_num="score"` behaves like `force_num=["score"]`.
- Lists and tuples are accepted; invalid non-string scalar types raise `ValueError`.
- Feature name `index` is reserved. Sweetviz renames an input column named `index` to `df_index`, and `FeatureConfig` performs the same `index` -> `df_index` normalization for all four lists.
- `get_all_mentioned_features()` returns the combined normalized features from `skip`, `force_cat`, `force_text`, and `force_num`.
- `get_predetermined_type(feature_name)` returns the preselected Sweetviz type for one feature: skipped, categorical, text, numeric, or unknown. It is useful for debugging configuration, not for constructing reports by itself.

### Practical forcing patterns

```python
# PassengerId is uninformative; Age should remain numeric even if small fixtures
# have few distinct ages; Ticket should remain text.
feat_cfg = sv.FeatureConfig(
    skip="PassengerId",
    force_num=["Age"],
    force_text=["Ticket"],
)

# Numeric-looking category codes should be categorical.
feat_cfg = sv.FeatureConfig(force_cat=["zip_code", "product_code"])

# A real column named index must be referenced as index or df_index; both end up
# targeting Sweetviz's internal df_index name.
feat_cfg = sv.FeatureConfig(skip="index")
```

Feature forcing does not perform arbitrary parsing. For example, `force_num` does not make arbitrary text numeric; clean first with pandas, such as `pd.to_numeric(series, errors="coerce")`, then handle any resulting missing values.

## Config parser overrides

Sweetviz loads package defaults into `sweetviz.config_parser`. Override them by reading an INI before constructing reports:

```python
import sweetviz as sv

sv.config_parser.read("sweetviz_override.ini")
report = sv.analyze(df, target_feat="target", feat_cfg=feat_cfg, pairwise_analysis="off")
```

Rules:

- Include each section header exactly, such as `[General]`; values without a section header are ignored by the INI parser.
- Load overrides before creating a report, because report construction and rendering read many defaults early.
- Use `scripts/write_sweetviz_override.py` to produce a safe starter template.
- The optional Comet.ml settings below control report layout for Comet output only; Comet upload itself requires external `comet_ml` installation and credentials.

### Default sections and stable keys

| Section | Keys and default values | Notes |
| --- | --- | --- |
| `[General]` | `default_verbosity = full`; `use_cjk_font = 0`; `association_min_to_bold = 0.1` | Use `default_verbosity = full`, `progress_only`, or `off`. Set `use_cjk_font = 1` to prefer bundled CJK-capable fonts for plots. |
| `[Output_Defaults]` | `html_layout = widescreen`; `html_scale = 1.0`; `notebook_layout = vertical`; `notebook_scale = 1.0`; `notebook_width = 100%%`; `notebook_height = 750` | Layout values accepted by rendering are `widescreen` and `vertical`. Percent signs are doubled in INI templates. |
| `[Type_Detection]` | `max_numeric_distinct_to_be_categorical = 10`; `max_text_distinct_to_be_categorical = 101`; `max_text_fraction_distinct_to_be_categorical = 0.33` | These thresholds decide numeric/category/text inference when no `FeatureConfig` override applies. |
| `[Processing]` | `association_auto_threshold = 200` | With `pairwise_analysis='auto'`, reports warn and return early above this many analyzed features; pass `pairwise_analysis='on'` or `'off'` explicitly for large data. |
| `[Layout]` | `show_logo = 1`; `full_page_padding_widescreen = 160`; `full_page_padding_vertical = 300`; `character_width_estimate = 6`; `summary_text_max_width = 618`; `pair_spacing = 84`; `col_spacing = 15`; `summary_top = 150`; `summary_spacing = 0`; `summary_height_per_element = 162`; `summary_vertical_detail_pos = 157`; `summary_vertical_padding = 8`; `cat_detail_graph_y = 75`; `cat_detail_breakdown_y_offset = 9`; `cat_detail_col_1_max_x = 217`; `cat_detail_col_x_padding_after_name = 30`; `cat_detail_col_target_extra_spacing = 15`; `cat_detail_col_spacing = 81`; `num_detail_max_listed_values = 15`; `detail_text_max_width = 800` | Most users only change `show_logo`. Other values are layout geometry and should be changed cautiously. |
| `[comet_ml_defaults]` | `html_layout = vertical`; `html_scale = 0.9` | Used when Comet-friendly HTML is generated. This does not install, authenticate, or upload to Comet.ml. |

### Minimal override examples

Quiet report construction by default:

```ini
[General]
default_verbosity = off
```

CJK-compatible plot font plus vertical HTML defaults:

```ini
[General]
use_cjk_font = 1

[Output_Defaults]
html_layout = vertical
html_scale = 0.9
```

Keep small numeric fixtures numeric by raising or lowering thresholds deliberately:

```ini
[Type_Detection]
max_numeric_distinct_to_be_categorical = 2
```

## Type inference rules

Sweetviz determines a feature type after pandas has loaded or prepared the column, unless `FeatureConfig` forces a supported conversion.

1. Mixed pandas inferred types are rejected. If value-count indexes report an inferred type that starts with `mixed`, Sweetviz raises a `TypeError` and asks you to convert the column to a single representation.
2. All-missing source-only columns start as `ALL_NAN` internally and settle to text for analysis. In comparisons, an all-missing side inherits the other side's type when possible; if both sides are all missing, both settle to text.
3. Boolean detection comes before numeric and categorical detection:
   - bool dtype is boolean;
   - numeric dtype with one or two non-null distinct values all between 0 and 1 is boolean;
   - two-value text combinations like `y`/`n`, `yes`/`no`, `true`/`false`, or `t`/`f` are boolean.
4. Numeric dtype with more than `[Type_Detection] max_numeric_distinct_to_be_categorical` non-null distinct values is numeric.
5. Numeric dtype with at most that threshold is categorical unless forced numeric or the threshold is changed.
6. Pandas categorical dtype is categorical.
7. Text/object data is categorical only when both limits are satisfied: distinct count is at most `max_text_distinct_to_be_categorical` and distinct fraction is at most `max_text_fraction_distinct_to_be_categorical`. Otherwise it is text.

Supported force/coercion patterns are intentionally limited:

- text -> categorical;
- categorical/bool -> text;
- numeric -> categorical;
- numeric -> text;
- categorical/bool -> numeric only when the series is already numeric-compatible.

If forcing fails, clean the pandas dtype first rather than trying to make Sweetviz parse ambiguous data.

## Preflight checklist

Run this checklist before report construction:

- [ ] Source dataframe has unique column names.
- [ ] Compare dataframe, if present, has unique column names.
- [ ] If a real column named `index` exists, downstream feature names are treated as `df_index`; avoid having both `index` and `df_index` because renaming can create ambiguity.
- [ ] Every `skip`, `force_cat`, `force_text`, and `force_num` feature exists in the source dataframe after `index` normalization.
- [ ] Target exists in source after `index` normalization.
- [ ] Target is not present in the `skip` list.
- [ ] Target has no missing values in source, and no missing values in compare if compare also has that target column.
- [ ] Target is numeric or boolean, not categorical or text.
- [ ] `compare_intra()` condition is boolean, has the same length as the source dataframe, and produces non-empty true and false groups.
- [ ] Large/wide data uses an explicit `pairwise_analysis='on'` or `'off'` decision instead of relying on `auto` above the configured threshold.
- [ ] Desired verbosity is configured through `[General] default_verbosity`, not as a public `analyze()`/`compare()` keyword.

For CSV-based checks, run:

```bash
python scripts/validate_sweetviz_inputs.py --source-csv data.csv --target target --force-num score
```
