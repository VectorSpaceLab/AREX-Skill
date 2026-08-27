# Performance API Reference

This reference records the NannyML 0.13.1 performance-related public API surface verified from source and installed package inspection.

## Problem types

Use one of these exact strings:

- `classification_binary`
- `classification_multiclass`
- `regression`

`CBPE` supports binary and multiclass classification. `DLE` supports regression. `PerformanceCalculator` supports binary classification, multiclass classification, and regression.

## `CBPE`

```python
nannyml.CBPE(
    metrics,
    y_pred_proba,
    y_true,
    problem_type,
    y_pred=None,
    timestamp_column_name=None,
    chunk_size=None,
    chunk_number=None,
    chunk_period=None,
    chunker=None,
    calibration='isotonic',
    calibrator=None,
    thresholds=None,
    normalize_confusion_matrix=None,
    business_value_matrix=None,
    normalize_business_value=None,
)
```

Use `CBPE` to estimate classification performance from model outputs when analysis targets are absent.

### Required columns

- Reference data needs `y_true` plus prediction probabilities and any configured `y_pred`.
- Analysis data needs prediction probabilities and any configured `y_pred`; analysis targets are not required for estimation.
- Binary `y_pred_proba` is a single string column name.
- Multiclass `y_pred_proba` is a mapping from class label to probability column name:

```python
y_pred_proba = {
    'prepaid_card': 'y_pred_proba_prepaid_card',
    'highstreet_card': 'y_pred_proba_highstreet_card',
    'upmarket_card': 'y_pred_proba_upmarket_card',
}
```

### Supported metrics

Classification CBPE metrics:

- `roc_auc`
- `f1`
- `average_precision`
- `precision`
- `recall`
- `specificity`
- `accuracy`
- `confusion_matrix`
- `business_value`

`confusion_matrix` expands into `true_positive`, `true_negative`, `false_positive`, and `false_negative` components. Filter by either the aggregate metric name or an individual component name when supported by the result object.

### Calibration

- Default calibration strategy is `calibration='isotonic'` through `CalibratorFactory.create('isotonic')`.
- A custom calibrator can be passed via `calibrator=`.
- `NoopCalibrator` returns prediction probabilities unchanged.
- `needs_calibration(y_true, y_pred_proba, calibrator, bin_count=10, split_count=10)` decides whether calibration improves expected calibration error.
- CBPE stores an uncalibrated copy internally before estimating so realized-threshold calculations can still use the original scores.

## `DLE`

```python
nannyml.DLE(
    feature_column_names,
    y_pred,
    y_true,
    timestamp_column_name=None,
    chunk_size=None,
    chunk_number=None,
    chunk_period=None,
    chunker=None,
    metrics=None,
    hyperparameters=None,
    tune_hyperparameters=False,
    hyperparameter_tuning_config=None,
    thresholds=None,
)
```

Use `DLE` to estimate regression performance from features and predictions before analysis targets are available. DLE trains internal LightGBM regressors that predict per-observation loss.

### Required columns

- Reference data needs every `feature_column_names` entry, `y_pred`, and `y_true`.
- Analysis data needs the same feature columns and `y_pred`; analysis `y_true` is not required for estimation.
- Categorical and continuous features are inferred from pandas dtypes. NannyML encodes categorical features internally.
- If pandas gives the categorical columns an Arrow-backed string dtype, disable pandas future string inference before loading data or use a pandas version that keeps these columns as object/category. Casting the final input columns to `object` or `category` is still recommended.

### Supported metrics

If `metrics=None`, DLE defaults to all supported regression metrics:

- `mae`
- `mape`
- `mse`
- `rmse`
- `msle`
- `rmsle`

For log-based metrics (`msle`, `rmsle`), make sure the data and predictions are compatible with logarithmic loss assumptions; negative predictions are a common source of downstream issues.

### Hyperparameters

- `tune_hyperparameters=False` by default.
- When `tune_hyperparameters=True`, DLE uses FLAML with a default LightGBM-focused tuning configuration.
- Use a small `time_budget` for smoke tests; tuning is slower and not guaranteed to improve results.
- Use `hyperparameters={...}` to supply LightGBM regressor parameters directly.

## `PerformanceCalculator`

```python
nannyml.PerformanceCalculator(
    metrics,
    y_true,
    problem_type,
    y_pred=None,
    y_pred_proba=None,
    timestamp_column_name=None,
    thresholds=None,
    chunk_size=None,
    chunk_number=None,
    chunk_period=None,
    chunker=None,
    normalize_confusion_matrix=None,
    business_value_matrix=None,
    normalize_business_value=None,
)
```

Use `PerformanceCalculator` to calculate realized performance when targets are available.

### Required columns

- Reference data must contain `y_true`.
- Analysis data must contain `y_true`; if it is missing, calculation raises an `InvalidArgumentsException`.
- Classification workflows need `y_pred_proba`.
- Multiclass and regression workflows require `y_pred`; binary classification may omit `y_pred` only for `roc_auc` or `average_precision`.
- Performance calculation adds a `chunk`-level `targets_missing_rate` column in result data when analysis targets contain missing values.

### Supported metrics

Classification:

- `roc_auc`
- `f1`
- `precision`
- `recall`
- `specificity`
- `accuracy`
- `confusion_matrix`
- `business_value`
- `average_precision`

Regression:

- `mae`
- `mape`
- `mse`
- `msle`
- `rmse`
- `rmsle`

## Threshold and business-value options

Default metric thresholds are `StandardDeviationThreshold()` unless overridden.

```python
import nannyml as nml

thresholds = {
    'f1': nml.ConstantThreshold(lower=0.75, upper=None),
    'roc_auc': nml.StandardDeviationThreshold(std_lower_multiplier=2, std_upper_multiplier=None),
}
```

Confusion-matrix normalization accepts:

- `None`: raw estimated/calculated counts.
- `'all'`: normalize by all observations.
- `'true'`: normalize by true class totals.
- `'pred'`: normalize by predicted class totals.

Business value requires `business_value_matrix`:

```python
business_value_matrix = [[2, -5], [-10, 10]]  # binary example
```

For binary classification the matrix must have shape `(2, 2)`. For multiclass classification it must be square and match the number of classes. `normalize_business_value` accepts `None` or `'per_prediction'`.

## Result methods

- `fit(reference_df)` returns the fitted estimator/calculator.
- `estimate(analysis_df)` is used by `CBPE` and `DLE`.
- `calculate(analysis_with_targets_df)` is used by `PerformanceCalculator`.
- `result.filter(period='analysis', metrics=['roc_auc'])` selects metrics and periods.
- `result.to_df(multilevel=False)` flattens DataFrame columns.
- `result.plot()` returns a Plotly performance figure.
- `result.compare(other_result).plot()` compares two single-key results.

See [../../../references/results-and-plots.md](../../../references/results-and-plots.md) for shared result behavior.
