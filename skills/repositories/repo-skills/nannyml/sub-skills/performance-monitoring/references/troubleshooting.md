# Performance Troubleshooting

## Constructor and schema errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `unknown metric key` or `Metric ... is not supported` | Metric name is misspelled or incompatible with the selected API/problem type | Use the metric lists in [api-reference.md](api-reference.md). Remember DLE is regression-only and CBPE is classification-only. |
| `'y_pred' can not be 'None' for problem type classification_multiclass` | Multiclass classification needs predicted class labels | Include a `y_pred` column and pass `y_pred='...'`. |
| `Metrics ... require 'y_pred' to be set` | Binary classification omitted `y_pred` while selecting metrics other than `roc_auc` or `average_precision` | Add the prediction-label column or narrow metrics to score-only metrics. |
| `y_pred_proba must be a string for binary classification` | Binary CBPE or realized performance got a dict/list probability mapping | Pass a single probability-score column name for binary classification. |
| `y_pred_proba must be a dictionary for multiclass classification` | Multiclass workflow got one string probability column | Pass `{class_label: probability_column_name}` for every class. |
| `target data column ... not found` | Reference or analysis data lacks `y_true` for the selected workflow | For CBPE/DLE, reference needs targets. For realized performance, both reference and analysis need targets. |
| Empty-data error | Dataframe has no rows after filtering/joining | Inspect shapes after every join/filter and before calling `fit`, `estimate`, or `calculate`. |

## CBPE calibration issues

CBPE defaults to isotonic calibration. It decides whether calibration is useful by comparing expected calibration error before and after calibration in cross-validation folds.

Troubleshooting steps:

1. Confirm `y_pred_proba` values are numeric scores/probabilities and have no unexpected NaNs.
2. Confirm reference targets are binary for binary classification or class labels matching the multiclass mapping.
3. If the user intentionally wants no calibration, pass a `NoopCalibrator`:

```python
import nannyml as nml

estimator = nml.CBPE(
    metrics=['roc_auc'],
    y_pred_proba='y_pred_proba',
    y_true='repaid',
    problem_type='classification_binary',
    calibrator=nml.NoopCalibrator() if hasattr(nml, 'NoopCalibrator') else None,
)
```

If `NoopCalibrator` is not top-level in the installed package, import it from `nannyml.calibration`.

## Business value and confusion matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `business_value_matrix must be provided` | `business_value` metric selected without matrix | Pass a square matrix whose size matches the number of classes. |
| `business_value_matrix must have shape (2,2)` | Binary business-value matrix is not 2x2 | Use `[[TN_value, FP_value], [FN_value, TP_value]]` shape. |
| Matrix is not square or class count mismatch | Multiclass matrix does not match class count | Make matrix dimensions equal to the number of class labels in `y_pred_proba`. |
| Invalid `normalize_business_value` | Value other than `None` or `'per_prediction'` | Use `None` for chunk-total business value or `'per_prediction'` for per-record normalization. |
| Invalid `normalize_confusion_matrix` | Value not in the accepted set | Use `None`, `'all'`, `'true'`, or `'pred'`. |

## DLE regression issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| DLE is slow | It trains internal LightGBM models and may run FLAML if tuning is enabled | Keep `tune_hyperparameters=False` for normal smoke runs; if tuning is requested, set a small `time_budget`. |
| Feature-column missing error | `feature_column_names` include a column absent from reference or analysis data | Intersect feature list with actual columns and exclude `timestamp`, `y_pred`, and `y_true`. |
| Log-based metric failure or nonsensical values | `msle` / `rmsle` with negative targets or predictions | Remove log metrics, filter negative predictions for diagnostic examples, or choose `mae`/`mse`/`rmse`. |
| Categorical handling surprises | Pandas dtype inference determines categorical vs continuous preprocessing | Cast categorical columns intentionally before fitting if the defaults are wrong. |
| `ArrowStringArray` reshape failure | Pandas 3 / pyarrow string inference stored categorical columns as Arrow-backed strings and DLE tried to reshape them | Set `pd.options.future.infer_string = False` before loading data or use `pandas<3`, then keep categorical features as `object` or `category`. |

## Realized performance and target completeness

`PerformanceCalculator` calculates `targets_missing_rate` for each analysis chunk. If some targets are missing, metric values may be based on partial data. Use `result.to_df(multilevel=False)` and inspect target completeness before interpreting alerts.

```python
realized_df = realized.filter(period='analysis').to_df(multilevel=False)
print([c for c in realized_df.columns if 'targets_missing_rate' in c])
```

If the target column is missing entirely, `calculate` raises an error. Join targets first:

```python
analysis_with_targets = analysis.merge(analysis_targets, on='id')
```

## Comparison problems

`compare` plots one result key against one result key. Filter both sides:

```python
estimated_one = estimated.filter(period='analysis', metrics=['roc_auc'])
realized_one = realized.filter(period='analysis', metrics=['roc_auc'])
figure = estimated_one.compare(realized_one).plot()
```

If the comparison message says there are multiple metrics, inspect `len(result.keys())` for each side and filter more narrowly.

## When to route away

- If the symptom is about feature distribution changes rather than metric values, use [../../drift-monitoring/SKILL.md](../../drift-monitoring/SKILL.md).
- If the symptom is about invalid chunking or thresholds across several monitors, use [../../data-setup/SKILL.md](../../data-setup/SKILL.md).
- If the symptom is about YAML config or `nml run`, use [../../cli-and-automation/SKILL.md](../../cli-and-automation/SKILL.md).
