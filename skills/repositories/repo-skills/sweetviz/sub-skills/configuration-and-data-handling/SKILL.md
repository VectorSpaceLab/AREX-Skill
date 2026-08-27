---
name: configuration-and-data-handling
description: "Prepare pandas inputs and Sweetviz configuration for predictable
  reports and comparisons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sweetviz configuration and data handling

Use this sub-skill when a Sweetviz task mentions input preparation, `FeatureConfig`, forced feature types, config overrides, wrong type inference, duplicate columns, target validation, CJK font settings, or quiet/progress-only verbosity.

## Route first

- Actual `analyze(...).show_html()` or `show_notebook()` rendering belongs in `../report-generation/` after data and config are valid.
- Train/test comparison or `compare_intra()` split design belongs in `../dataset-comparison/`; use this sub-skill only for its shared validation and configuration pieces.
- Optional Comet.ml upload workflow details belong in `../report-generation/`; this sub-skill only covers `[comet_ml_defaults]` config defaults.

## Operating checklist

1. Normalize requested feature controls with `sweetviz.FeatureConfig(skip=None, force_cat=None, force_text=None, force_num=None)`.
   - Strings become one-item feature lists; lists and tuples are accepted.
   - A feature literally named `index` is normalized to `df_index`, matching Sweetviz's reserved-name handling.
   - Use `get_predetermined_type(name)` only as an inspection/debug aid; report creation consumes the `FeatureConfig` object through `feat_cfg`.
2. Preflight pandas inputs before constructing the report.
   - No duplicate columns in source or compare dataframes.
   - Every `FeatureConfig` column must exist in the source dataframe after `index` normalization.
   - A target must exist in source, must not be skipped, must not contain missing values, and must be numeric or boolean.
   - If compare data has the target column, that compare target also must not contain missing values.
   - `compare_intra()` conditions must be boolean and split into non-empty true and false groups.
3. Decide type-detection overrides.
   - Numeric columns with at most the configured numeric-distinct threshold infer as categorical by default.
   - High-cardinality text remains text unless forced categorical; forcing can make reports heavier or less useful.
   - Mixed inferred pandas types are unsupported; clean to a single dtype before using Sweetviz.
4. Apply config overrides before report construction.
   - Load an INI with `sweetviz.config_parser.read("your_override.ini")` before calling `analyze`, `compare`, or `compare_intra`.
   - Do not pass `verbosity=` to public `analyze()` or `compare()` in Sweetviz 2.3.3; those public signatures accept `source`, target/config, and `pairwise_analysis` only. Use `[General] default_verbosity` in a config override, or the advanced `DataframeReport(..., verbosity=...)` constructor when appropriate.

## Bundled references and helpers

- Read `references/data-and-config-reference.md` for `FeatureConfig` examples, config sections, type inference rules, and the preflight checklist.
- Read `references/troubleshooting.md` for duplicate columns, mixed types, wrong inference, target errors, invalid layout/verbosity, and font/package-asset symptoms.
- Use `scripts/validate_sweetviz_inputs.py --help` to preflight CSV files without generating a Sweetviz report.
- Use `scripts/write_sweetviz_override.py --help` to create a deterministic Sweetviz override INI template without importing Sweetviz.
