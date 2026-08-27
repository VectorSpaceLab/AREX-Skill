---
name: dataset-comparison
description: "Compare two pandas DataFrames or two subsets of one DataFrame with
  Sweetviz, including target-aware validation and deterministic HTML output
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dataset Comparison

Use this sub-skill when the task asks for Sweetviz comparison, train/test profiling, dataset drift/profile comparison, or subgroup comparison such as "male vs female". It owns `sweetviz.compare()` and `sweetviz.compare_intra()` guidance only.

## Route here when

- Comparing two existing pandas DataFrames, usually train/test, baseline/current, or reference/candidate.
- Splitting one DataFrame into two named groups with a boolean condition and comparing the groups.
- The comparison includes a target feature and needs validation before rendering.
- The user mentions `compare`, `compare_intra`, subgroup split, non-boolean condition, empty split, or compare-only columns.

## Route elsewhere

- Single-DataFrame `sweetviz.analyze()` or render-only/browser/notebook details: use the `report-generation` sub-skill.
- Detailed `FeatureConfig`, type forcing, config override files, duplicate-column cleanup, or input preflight beyond comparison-specific checks: use the `configuration-and-data-handling` sub-skill.
- Install/import/package-data/font issues: use the Sweetviz root troubleshooting reference.

## Operating flow

1. Choose the constructor:
   - `sweetviz.compare([source_df, "Source name"], [compare_df, "Compare name"], target_feat=..., feat_cfg=..., pairwise_analysis=...)` for two DataFrames.
   - `sweetviz.compare_intra(source_df, condition_series, ["True group", "False group"], target_feat=..., feat_cfg=..., pairwise_analysis=...)` for a split of one DataFrame.
2. Validate comparison inputs before constructing the report:
   - No duplicate columns in either DataFrame.
   - `compare_intra` condition has the same length as `source_df`, has plain boolean dtype, and creates non-empty true and false groups.
   - Target feature exists in the source, is not skipped, is numeric or boolean, and has no missing values. If the compare DataFrame also contains the target, it must also have no missing values.
   - Any names used in `FeatureConfig` are case-sensitive and must be present in the source DataFrame.
3. Prefer explicit dataset names (`[df, "Training Data"]` or `(df, "Training Data")`) so report sections are interpretable.
4. Pick `pairwise_analysis`: use `"off"` for deterministic or wide smoke runs, `"auto"` for ordinary small reports, and `"on"` only when association cost is acceptable.
5. Render with `report.show_html(..., open_browser=False)` for automated work and validate the output file exists and is non-empty. For layout/browser/notebook choices, defer to `report-generation`.

## Bundled references and helper

- [Comparison workflows](references/workflows.md): train/test and `compare_intra` recipes with tiny schemas and deterministic output validation.
- [API reference](references/api-reference.md): verified signatures, accepted input shapes, naming, target/config interactions, pairwise behavior, and column mismatch notes.
- [Troubleshooting](references/troubleshooting.md): non-boolean conditions, empty splits, duplicate columns, target NaNs, missing `FeatureConfig` names, and pairwise threshold behavior.
- [Smoke script](scripts/sweetviz_compare_smoke.py): offline argparse helper that builds tiny fixtures, runs `compare` and/or `compare_intra`, writes HTML without opening a browser, and can demonstrate invalid non-boolean conditions.

## Non-goals and cautions

- Do not pass `verbosity` to `sweetviz.compare()` or `sweetviz.compare_intra()`; their public signatures do not accept it. If progress output must be controlled, use Sweetviz configuration defaults or the lower-level report class guidance from the configuration/reporting sub-skills.
- Do not use maintainer or network-update helpers for end-user EDA comparison workflows.
- Optional Comet.ml logging is credentialed external behavior owned by reporting guidance; do not require it for comparison verification.
