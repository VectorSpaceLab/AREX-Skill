# Drift Troubleshooting

## Univariate drift errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing-column `InvalidArgumentsException` | A `column_names` entry is absent from reference or analysis data | Print columns for both dataframes and pass only shared monitored columns. |
| A numeric categorical column uses continuous methods | Pandas dtype inference treated it as numeric | Pass it in `treat_as_categorical`. |
| A continuous score column uses categorical methods | Column dtype is object/category or was forced categorical | Cast to numeric or pass it in `treat_as_numerical`. |
| Custom `chi2` threshold appears ignored | `chi2` does not support custom thresholds in this version | Use the default `chi2` p-value thresholding or choose a distance method such as `jensen_shannon`, `hellinger`, or `l_infinity`. |
| Distribution plot fails or is too busy | Too many columns/methods selected | Filter to one or a few columns before `plot(kind='distribution')`. |
| Period-based chunking fails | Timestamp column missing or not parseable | Add `timestamp_column_name`, verify pandas parsing, or use size/count chunking. |

## Multivariate drift errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| PCA drift fails on missing columns | `column_names` includes non-feature columns or absent columns | Build the feature list explicitly and exclude IDs, timestamps, targets, predictions, and period labels unless intentionally monitored. |
| PCA drift raises imputer type/strategy errors | Custom imputers are not `sklearn.impute.SimpleImputer` instances or categorical strategy is unsupported | Use `SimpleImputer(strategy='most_frequent')` for categorical columns and mean/median-style imputers for continuous columns. |
| Reconstruction error is hard to interpret | PCA gives one aggregate score, not per-feature root cause | Pair with univariate drift and ranking to identify candidate drivers. |
| Domain classifier is slow | It trains LightGBM classifiers with cross-validation per chunk | Increase chunk size, reduce feature count, keep `tune_hyperparameters=False`, or switch to PCA reconstruction-error drift for a cheaper aggregate score. |
| Domain-classifier threshold seems asymmetric | Default threshold is `ConstantThreshold(lower=0.45, upper=0.65)` | Interpret values around 0.5 as no separability; values above upper threshold as drift alerts. |

## Ranking errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `rankable_result contains no data` | Result was filtered to an empty period/column/method set | Inspect `result.to_df()` before ranking and adjust filters. |
| `Only one categorical drift method should be present` | Univariate result contains multiple categorical methods | Filter with `methods=['jensen_shannon']` or another single categorical method. |
| `Only one continuous drift method should be present` | Univariate result contains multiple continuous methods | Filter with a single continuous method. |
| `Estimated or Realized Performance results object required` | `CorrelationRanker.fit` or `rank` got a non-performance result | Pass a filtered CBPE, DLE, or PerformanceCalculator result for performance. |
| `Just one metric should be present` | Performance result contains multiple metrics | Filter performance results with `metrics=['roc_auc']` or one chosen metric. |
| `NotFittedException` or ranker not fitted | `CorrelationRanker.rank` called before `fit` | Call `ranker.fit(reference_performance.filter(period='reference', metrics=[...]))` first. |
| Period mismatch error | Drift and performance inputs are filtered to different periods | Filter both to `period='analysis'`, `period='reference'`, or `period='all'` consistently. |

## Output and target drift mistakes

- Output drift does not require targets. Use prediction labels and/or scores as monitored columns.
- Target drift requires target labels in reference and analysis data.
- For binary targets/predictions that are integer labels, explicitly pass `treat_as_categorical` when you want categorical drift methods.
- For regression predictions/targets, keep them continuous and use continuous methods.

## Method-selection pitfalls

- `jensen_shannon` is a practical default because it works for both continuous and categorical features.
- `wasserstein` can be sensitive to magnitude and extreme continuous tails.
- `hellinger` and `jensen_shannon` can saturate when distributions are already disjoint.
- `l_infinity` focuses on maximum categorical proportion differences.
- `kolmogorov_smirnov` / `chi2` are statistical-test oriented; significance can depend strongly on sample size.

## If drift and performance disagree

A drift alert does not always mean performance degradation, and a performance drop can occur without a clear univariate drift alert. To investigate:

1. Estimate or calculate one performance metric with [../../performance-monitoring/SKILL.md](../../performance-monitoring/SKILL.md).
2. Filter drift to one method and candidate columns.
3. Use `CorrelationRanker` or `result.compare` to prioritize follow-up.
4. Inspect data-quality and summary-stat results from [../../data-setup/SKILL.md](../../data-setup/SKILL.md) for missing/unseen/out-of-range signals that may explain drift.
