# Drift Methods and API Reference

This reference records NannyML 0.13.1 drift APIs and method-selection rules.

## `UnivariateDriftCalculator`

```python
nannyml.UnivariateDriftCalculator(
    column_names,
    treat_as_numerical=None,
    treat_as_categorical=None,
    timestamp_column_name=None,
    categorical_methods=None,
    continuous_methods=None,
    chunk_size=None,
    chunk_number=None,
    chunk_period=None,
    chunker=None,
    thresholds=None,
    computation_params=None,
)
```

### Supported methods

| Feature type | Methods |
| --- | --- |
| Continuous | `kolmogorov_smirnov`, `jensen_shannon`, `wasserstein`, `hellinger` |
| Categorical | `chi2`, `jensen_shannon`, `l_infinity`, `hellinger` |

If `continuous_methods` or `categorical_methods` is omitted, NannyML defaults to `['jensen_shannon']` for that feature type.

### Feature typing

NannyML splits features into continuous and categorical using pandas dtypes. Override this when semantic type differs from dtype:

```python
calc = nml.UnivariateDriftCalculator(
    column_names=['zip_code', 'score_bucket', 'income'],
    treat_as_categorical=['zip_code', 'score_bucket'],
    treat_as_numerical=['income'],
    categorical_methods=['jensen_shannon', 'l_infinity'],
    continuous_methods=['kolmogorov_smirnov', 'wasserstein'],
)
```

Use output drift by treating prediction columns like normal columns:

```python
output_drift = nml.UnivariateDriftCalculator(
    column_names=['y_pred', 'y_pred_proba'],
    treat_as_categorical=['y_pred'],
    timestamp_column_name='timestamp',
)
```

Use target drift only after targets are available:

```python
target_drift = nml.UnivariateDriftCalculator(
    column_names=['y_true'],
    timestamp_column_name='timestamp',
).fit(reference_with_targets).calculate(analysis_with_targets)
```

### Thresholds and computation parameters

Default thresholds are `StandardDeviationThreshold(std_lower_multiplier=None)` for supported univariate methods. This means only the upper side is used by default. The `chi2` method currently ignores custom threshold overrides and logs/warns that it does not support custom thresholds yet.

`computation_params` applies to `kolmogorov_smirnov` and `wasserstein`:

```python
computation_params = {
    'kolmogorov_smirnov': {'calculation_method': 'auto', 'n_bins': 10000},
    'wasserstein': {'calculation_method': 'estimated', 'n_bins': 10000},
}
```

`calculation_method` can be `auto`, `exact`, or `estimated`.

## `DataReconstructionDriftCalculator`

```python
nannyml.DataReconstructionDriftCalculator(
    column_names,
    timestamp_column_name=None,
    n_components=0.65,
    chunk_size=None,
    chunk_number=None,
    chunk_period=None,
    chunker=None,
    imputer_categorical=None,
    imputer_continuous=None,
    threshold=nannyml.StandardDeviationThreshold(),
)
```

This multivariate detector uses PCA reconstruction error on all selected columns. Internally it:

1. Splits selected columns into categorical and continuous groups.
2. Imputes categorical missing values with most frequent values by default.
3. Imputes continuous missing values with mean values by default.
4. Count-encodes categorical columns.
5. Scales features.
6. Fits PCA on reference data and monitors reconstruction error by chunk.

Result metric key: `reconstruction_error`.

Use this when subtle multivariate changes matter and a single less-explainable score is acceptable.

## `DomainClassifierCalculator`

```python
nannyml.DomainClassifierCalculator(
    feature_column_names,
    treat_as_categorical=None,
    timestamp_column_name=None,
    chunk_size=None,
    chunk_number=None,
    chunk_period=None,
    chunker=None,
    cv_folds_num=5,
    hyperparameters=DEFAULT_LGBM_HYPERPARAMS,
    tune_hyperparameters=False,
    hyperparameter_tuning_config=DEFAULT_LGBM_HYPERPARAM_TUNING_CONFIG,
    threshold=nannyml.ConstantThreshold(lower=0.45, upper=0.65),
)
```

This multivariate detector trains a classifier to distinguish reference rows from each chunk. The output is AUROC-like separability:

- Around `0.5`: reference and chunk are difficult to distinguish.
- High values toward `1.0`: chunk is distinguishable from reference.
- Default alerting uses `ConstantThreshold(lower=0.45, upper=0.65)`.

Domain-classifier drift uses LightGBM and can be more expensive than PCA. Keep `tune_hyperparameters=False` unless the user explicitly requests tuning.

## Rankers

### `AlertCountRanker`

```python
nannyml.AlertCountRanker().rank(rankable_result, only_drifting=False)
```

Inputs can be univariate drift, missing-values, unseen-values, or summary-stat result objects. For univariate drift, filter to only one categorical method and one continuous method before ranking.

Output columns include:

- `number_of_alerts`
- `column_name`
- `rank`

### `CorrelationRanker`

```python
ranker = nannyml.CorrelationRanker()
ranker.fit(reference_performance_calculation_result)
ranking = ranker.rank(rankable_result, performance_result, only_drifting=False)
```

Inputs must be filtered to one performance metric and one drift/data-quality/stat key per column. The ranker computes correlation with absolute changes in the selected performance metric.

## Result and plot behavior

- Univariate result filters: `period`, `column_names`, and `methods`.
- Univariate plot kinds: `kind='drift'` and `kind='distribution'`.
- Multivariate result filters: period and metric-like result key.
- Multivariate plot kind: `kind='drift'`.
- All result objects support `to_df(multilevel=False)` for easier inspection.

## Method-selection heuristics

- Start with `jensen_shannon` when the user needs a robust default for both continuous and categorical columns.
- Add `kolmogorov_smirnov` for continuous statistical-test behavior and p-value-style sensitivity.
- Add `wasserstein` for continuous magnitude-sensitive shifts, especially location shifts and tail movement.
- Add `hellinger` when distribution overlap is the intended interpretation.
- Add `l_infinity` for categorical maximum-proportion shifts.
- Use `chi2` for categorical statistical testing, but do not promise custom-threshold behavior for it.
- Use PCA reconstruction-error drift for an aggregate multivariate alert with moderate runtime.
- Use domain-classifier drift when the task is explicitly about reference-vs-analysis separability and the runtime budget allows it.
