---
name: performance-monitoring
description: "Estimate and calculate NannyML model performance for
  classification and regression, including CBPE, DLE, realized metrics,
  calibration, and comparison workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Performance Monitoring

Use this sub-skill when the task is about model performance in NannyML: estimating performance before analysis targets are available, calculating realized performance after targets arrive, comparing estimated and realized performance, selecting performance metrics, diagnosing calibration, or using confusion-matrix/business-value metrics.

Route drift detection, ranking, data-quality checks, chunking basics, and CLI automation elsewhere unless they are directly needed to complete a performance workflow.

## Quick routing

- Read [references/workflows.md](references/workflows.md) for end-to-end CBPE, DLE, realized-performance, and comparison recipes.
- Read [references/api-reference.md](references/api-reference.md) for constructor signatures, supported metrics, probability mapping rules, threshold inputs, and result methods.
- Read [references/troubleshooting.md](references/troubleshooting.md) when errors mention missing `y_pred`, `y_pred_proba`, `y_true`, unsupported metrics, calibration, business-value matrix shape, invalid problem type, target completeness, or log-based regression metrics.
- Read the root [../../references/results-and-plots.md](../../references/results-and-plots.md) when the user asks about `filter`, `to_df`, `plot`, or `compare` behavior.
- Read the root [../../references/datasets.md](../../references/datasets.md) to pick a built-in dataset for a quick example.

## Choose the right performance API

| Task | Use | Requires |
| --- | --- | --- |
| Estimate binary or multiclass classification performance without analysis targets | `nannyml.CBPE` | Reference targets; prediction probabilities; `y_pred` for most classification metrics |
| Estimate regression performance without analysis targets | `nannyml.DLE` | Reference targets; prediction column; feature columns; LightGBM/FLAML dependencies |
| Calculate realized performance when targets are available | `nannyml.PerformanceCalculator` | Targets in reference and analysis; predictions/probabilities according to metric/problem type |
| Compare estimated and realized results | `result.filter(...).compare(other.filter(...)).plot()` | Both result sides filtered to one metric/key |

## Minimal binary CBPE example

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_dataset()

estimator = nml.CBPE(
    metrics=['roc_auc', 'f1'],
    y_pred_proba='y_pred_proba',
    y_pred='y_pred',
    y_true='repaid',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
)
estimator.fit(reference)
estimated = estimator.estimate(analysis)
print(estimated.filter(period='analysis', metrics=['roc_auc']).to_df(multilevel=False).head())
```

## Minimal regression DLE example

```python
import pandas as pd
import nannyml as nml

# NannyML 0.13.1 can hit ArrowStringArray issues under pandas 3 string inference.
if hasattr(pd.options, 'future') and hasattr(pd.options.future, 'infer_string'):
    pd.options.future.infer_string = False

reference, analysis, _ = nml.load_synthetic_car_price_dataset()
features = ['car_age', 'km_driven', 'price_new', 'accident_count', 'door_count', 'fuel', 'transmission']

# Keep string-like categorical columns as object/category before fitting.
for column in ['fuel', 'transmission']:
    reference[column] = reference[column].astype('object')
    analysis[column] = analysis[column].astype('object')

estimator = nml.DLE(
    feature_column_names=features,
    y_pred='y_pred',
    y_true='y_true',
    metrics=['rmse', 'rmsle'],
    timestamp_column_name='timestamp',
    chunk_size=6000,
)
estimator.fit(reference)
estimated = estimator.estimate(analysis)
print(estimated.filter(period='analysis', metrics=['rmse']).to_df(multilevel=False).head())
```

## Minimal realized-performance example

```python
import nannyml as nml

reference, analysis, analysis_targets = nml.load_synthetic_car_loan_dataset()
analysis_with_targets = analysis.merge(analysis_targets, on='id')

calculator = nml.PerformanceCalculator(
    metrics=['roc_auc', 'f1'],
    y_true='repaid',
    y_pred='y_pred',
    y_pred_proba='y_pred_proba',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
)
calculator.fit(reference)
realized = calculator.calculate(analysis_with_targets)
print(realized.filter(period='analysis', metrics=['f1']).to_df(multilevel=False).head())
```

## Decision points

- Use `classification_binary`, `classification_multiclass`, or `regression` exactly as the `problem_type` value.
- For multiclass tasks, pass `y_pred_proba` as a dictionary mapping class labels to probability column names.
- `y_pred` may be omitted only for binary classification metrics `roc_auc` and `average_precision`. Other metrics and all multiclass/regression workflows need `y_pred`.
- Use `CBPE` only for classification and `DLE` only for regression estimation.
- Use `PerformanceCalculator` when actual targets are available and the user asks for realized performance.
- Use `thresholds={metric_name: nml.ConstantThreshold(...)}` or `nml.StandardDeviationThreshold(...)` for custom alert behavior.
- For `confusion_matrix`, choose `normalize_confusion_matrix=None`, `'all'`, `'true'`, or `'pred'`.
- For `business_value`, provide a square business-value matrix and optionally `normalize_business_value='per_prediction'`.

## Route elsewhere

- Feature drift, output drift, target drift, PCA/domain-classifier drift, or drift ranking -> [../drift-monitoring/SKILL.md](../drift-monitoring/SKILL.md)
- Reference/analysis data layout, chunking, thresholds, data-quality calculators, or built-in datasets -> [../data-setup/SKILL.md](../data-setup/SKILL.md)
- YAML configuration, `nml run`, scheduling, stores, or writers -> [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md)
