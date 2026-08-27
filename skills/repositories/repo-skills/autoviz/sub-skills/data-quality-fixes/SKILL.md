---
name: data-quality-fixes
description: "Use AutoViz data-quality reports and FixDQ to inspect and repair
  tabular data issues."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data Quality Fixes

Use this sub-skill when the user asks about `FixDQ`, `data_cleaning_suggestions`, duplicate rows, mixed data types, infinities, rare categories, leakage, skew, outliers, or data-cleaning advice that appears during an AutoViz run.

## Use this when

- The prompt names `FixDQ`, `Fix_DQ`, `data_cleaning_suggestions`, or `dq_report`.
- AutoViz prints data-quality warnings before plotting.
- The user wants a transformer-like cleanup step they can reuse on train/test data.
- The user is debugging `pandas_dq`, pandas compatibility, or missing `IPython.display`.
- The user wants to know whether a noisy dataset should be cleaned before plotting.

## Core flow

1. Start with a pandas DataFrame.
2. Use `data_cleaning_suggestions(df, target=target)` for a report-style inspection.
3. Use `FixDQ()` when the user wants a fit/transform style cleaning object.
4. Keep target handling explicit: pass a target column name, a target list, `""`, or `None` according to the user's problem.
5. After cleaning, hand the resulting DataFrame back to the EDA sub-skill for visualization.
6. When the user only wants diagnosis, stop at the report and explain the result in plain language.

## Read these references

- [`references/workflows.md`](references/workflows.md): report and transformer recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md): pandas, `IPython`, and `pandas_dq` compatibility notes.
- [`../../references/install-and-compatibility.md`](../../references/install-and-compatibility.md): package-version guidance.
- [`../../references/api-reference.md`](../../references/api-reference.md): signatures for `FixDQ` and `data_cleaning_suggestions`.
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md): cross-cutting environment issues that can break the report path.

## Use these scripts

- Run [`scripts/fixdq_smoke.py`](scripts/fixdq_smoke.py) to verify that `FixDQ` and `data_cleaning_suggestions` can be imported and exercised on a tiny DataFrame.
- If the failure is really plot rendering or `chart_format`, switch to the EDA sub-skill and run its smoke script.
- If the failure looks like a package install issue, run [`../../scripts/inspect_install.py`](../../scripts/inspect_install.py) first.

## Important compatibility facts

- `data_cleaning_suggestions` delegates to `pandas_dq.dq_report`.
- This repository version works with pandas 2.x; pandas 3.x removed `DataFrame.applymap`, which can break `pandas_dq`.
- `pandas_dq` imports `IPython.display`, so a non-notebook environment may still need `IPython` installed.
- `FixDQ.__init__` accepts `quantile`, `cat_fill_value`, `num_fill_value`, `rare_threshold`, and `correlation_threshold`.
- The report path is still useful even when the user never wants plots.

## Issues the report can surface

- duplicate rows or duplicate columns
- zero-variance features
- rare categories
- high-cardinality features
- infinite values
- mixed Python types in a single column
- skewed distributions
- highly correlated features or leakage
- imbalanced classes
- target-related issues when a target column is supplied

## Cross-routing

- If the user asks for saved charts or automated EDA plots after cleaning, route to [`../eda-visualization/SKILL.md`](../eda-visualization/SKILL.md).
- If the data-quality issue is specific to long text columns or wordcloud behavior, route to [`../text-wordclouds/SKILL.md`](../text-wordclouds/SKILL.md).
- Keep dependency/environment fixes in references; do not leak private inspection-environment paths.
- If the user wants to apply the same cleanup to train and test data, emphasize `FixDQ` over the report-only helper.

## Troubleshooting reminders

- If the report fails at import time, check `IPython` first, then `pandas` version, then XGBoost/setuptools interactions.
- If a tiny sample gives odd warnings, explain that the dataset may be too small to classify reliably.
- If the target column is missing or misspelled, verify the exact column name before retrying.
- If the result object is a `Styler` or other display wrapper, describe that the report succeeded even if the object is not a plain DataFrame.

## Escalation

If the user wants to continue from the report into plotting, route back to the EDA sub-skill with the cleaned DataFrame.
If the user wants text-column advice rather than numeric or categorical cleanup, route to the text sub-skill instead of stretching this one.
