---
name: drift-monitoring
description: "Detect and interpret NannyML feature, output, target, and
  multivariate drift, then rank suspicious columns by alerts or performance
  correlation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Drift Monitoring

Use this sub-skill when the task is about NannyML drift detection: univariate feature drift, model output drift, target distribution drift, multivariate PCA reconstruction-error drift, multivariate domain-classifier drift, or ranking drifted columns for follow-up investigation.

Route model performance estimation/calculation to the performance sub-skill, data-quality-only checks to the data-setup sub-skill, and YAML/CLI orchestration to the CLI sub-skill.

## Quick routing

- Read [references/workflows.md](references/workflows.md) for univariate drift, output/target drift, PCA reconstruction-error drift, domain-classifier drift, and ranking recipes.
- Read [references/methods.md](references/methods.md) for supported drift methods, feature-type handling, default thresholds, result columns, and ranker constraints.
- Read [references/troubleshooting.md](references/troubleshooting.md) when errors mention missing columns, wrong categorical/continuous type, ignored `chi2` thresholds, one-method ranking requirements, not-fitted rankers, or domain-classifier runtime cost.
- Read [../../references/results-and-plots.md](../../references/results-and-plots.md) for `filter`, `to_df`, `plot`, distribution plots, and `compare` patterns.
- Read [../data-setup/SKILL.md](../data-setup/SKILL.md) for chunking, thresholds, and data requirements shared by drift workflows.

## Choose the right drift workflow

| Task | Use | Output |
| --- | --- | --- |
| Detect per-feature distribution changes | `nannyml.UnivariateDriftCalculator` | One drift metric per selected method/column/chunk |
| Detect drift in prediction labels or scores | `UnivariateDriftCalculator` on `y_pred` and/or `y_pred_proba` | Output drift over chunks |
| Detect target distribution drift after labels arrive | `UnivariateDriftCalculator` on `y_true` | Target drift over chunks |
| Detect multivariate drift with a single less-explainable score | `DataReconstructionDriftCalculator` | `reconstruction_error` per chunk |
| Detect distribution separability between reference and chunks | `DomainClassifierCalculator` | `domain_classifier_auroc` per chunk |
| Prioritize drifted features by alert count | `AlertCountRanker` | Ranking DataFrame with `number_of_alerts`, `column_name`, `rank` |
| Prioritize drifted features by correlation with performance change | `CorrelationRanker` | Ranking DataFrame with Pearson correlation and drift flags |

## Minimal univariate drift example

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_dataset()
features = ['car_value', 'salary_range', 'debt_to_income_ratio', 'loan_length', 'repaid_loan_on_prev_car', 'size_of_downpayment', 'driver_tenure']

calculator = nml.UnivariateDriftCalculator(
    column_names=features,
    timestamp_column_name='timestamp',
    continuous_methods=['jensen_shannon', 'wasserstein'],
    categorical_methods=['jensen_shannon', 'l_infinity'],
    chunk_size=5000,
)
result = calculator.fit(reference).calculate(analysis)
print(result.filter(period='analysis', methods=['jensen_shannon']).to_df(multilevel=False).head())
```

## Minimal multivariate drift example

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_dataset()
features = ['car_value', 'salary_range', 'debt_to_income_ratio', 'loan_length', 'repaid_loan_on_prev_car', 'size_of_downpayment', 'driver_tenure']

pca_drift = nml.DataReconstructionDriftCalculator(
    column_names=features,
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

print(pca_drift.filter(period='analysis').to_df(multilevel=False).head())
```

## Minimal ranking example

Filter univariate results to one method per feature before ranking.

```python
ranker = nml.AlertCountRanker()
ranking = ranker.rank(result.filter(period='analysis', methods=['jensen_shannon']), only_drifting=True)
print(ranking.head())
```

For correlation ranking, use one performance metric and one drift method:

```python
correlation_ranker = nml.CorrelationRanker()
correlation_ranker.fit(estimated_performance.filter(period='reference', metrics=['roc_auc']))
ranking = correlation_ranker.rank(
    result.filter(period='analysis', methods=['jensen_shannon']),
    estimated_performance.filter(period='analysis', metrics=['roc_auc']),
)
```

## Decision points

- Use univariate drift when explainability by feature or output column matters.
- Use PCA reconstruction-error drift when a single multivariate score is useful and less explainability is acceptable.
- Use domain-classifier drift when the user wants a separability-based multivariate score and accepts internal LightGBM/FLAML runtime cost.
- Use `treat_as_categorical` / `treat_as_numerical` to override pandas dtype inference when feature semantics are known.
- Use output drift on prediction labels/scores when targets are unavailable but model outputs may shift.
- Use target drift only when actual target labels are available.
- Ranking is a follow-up to univariate/data-quality/summary results; it is not a replacement for calculating drift.

## Route elsewhere

- CBPE, DLE, realized performance, or estimated-vs-realized comparison -> [../performance-monitoring/SKILL.md](../performance-monitoring/SKILL.md)
- Missing/unseen/range data-quality checks, summary statistics, chunking, thresholds, or built-in datasets -> [../data-setup/SKILL.md](../data-setup/SKILL.md)
- CLI config, scheduling, output writers, stores -> [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md)
