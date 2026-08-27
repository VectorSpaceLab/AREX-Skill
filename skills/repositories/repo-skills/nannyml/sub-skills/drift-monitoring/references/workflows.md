# Drift Monitoring Workflows

## Workflow 1: feature-level univariate drift

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_dataset()
features = ['car_value', 'salary_range', 'debt_to_income_ratio', 'loan_length', 'repaid_loan_on_prev_car', 'size_of_downpayment', 'driver_tenure']

calc = nml.UnivariateDriftCalculator(
    column_names=features,
    timestamp_column_name='timestamp',
    continuous_methods=['jensen_shannon', 'wasserstein'],
    categorical_methods=['jensen_shannon', 'l_infinity'],
    chunk_size=5000,
)
results = calc.fit(reference).calculate(analysis)

# Flat dataframe for assertions or logs
flat = results.filter(period='analysis', methods=['jensen_shannon']).to_df(multilevel=False)

# Drift plot for one column/method
figure = results.filter(column_names=['salary_range'], methods=['jensen_shannon']).plot(kind='drift')

# Distribution plot for one or more columns
figure = results.filter(period='analysis', column_names=['salary_range']).plot(kind='distribution')
```

## Workflow 2: type overrides for mixed columns

Use this when ID-like or integer columns should be categorical, or when numeric-looking categories should not be treated as continuous.

```python
calc = nml.UnivariateDriftCalculator(
    column_names=['customer_segment', 'zip_code', 'risk_score'],
    treat_as_categorical=['zip_code'],
    treat_as_numerical=['risk_score'],
    categorical_methods=['jensen_shannon', 'l_infinity'],
    continuous_methods=['kolmogorov_smirnov', 'wasserstein'],
    timestamp_column_name='timestamp',
    chunk_size=1000,
)
```

Keep overrides limited to columns listed in `column_names`.

## Workflow 3: model output drift

Output drift uses the same univariate calculator on prediction columns.

```python
reference, analysis, _ = nml.load_synthetic_binary_classification_dataset()

output_drift = nml.UnivariateDriftCalculator(
    column_names=['y_pred', 'y_pred_proba'],
    treat_as_categorical=['y_pred'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

print(output_drift.filter(period='analysis', methods=['jensen_shannon']).to_df(multilevel=False).head())
```

For regression output drift, use the prediction column as continuous:

```python
reference, analysis, _ = nml.load_synthetic_car_price_dataset()
regression_output_drift = nml.UnivariateDriftCalculator(
    column_names=['y_pred'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)
```

## Workflow 4: target distribution drift

Target drift requires target values for the analysis period.

```python
reference, analysis, analysis_targets = nml.load_synthetic_car_price_dataset()
analysis_with_targets = analysis.merge(analysis_targets, on='id')

target_drift = nml.UnivariateDriftCalculator(
    column_names=['y_true'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis_with_targets)
```

If analysis targets are unavailable, route to output drift or performance estimation instead of target drift.

## Workflow 5: multivariate PCA reconstruction-error drift

Use this to monitor an aggregate multivariate signal.

```python
reference, analysis, _ = nml.load_synthetic_car_loan_dataset()
features = ['car_value', 'salary_range', 'debt_to_income_ratio', 'loan_length', 'repaid_loan_on_prev_car', 'size_of_downpayment', 'driver_tenure']

pca_calc = nml.DataReconstructionDriftCalculator(
    column_names=features,
    timestamp_column_name='timestamp',
    n_components=0.75,
    chunk_size=5000,
)
pca_results = pca_calc.fit(reference).calculate(analysis)
print(pca_results.filter(period='analysis').to_df(multilevel=False).head())
```

PCA drift imputes missing values and encodes categorical features internally. It is less explainable than univariate drift, so pair it with univariate drift when the user needs root-cause investigation.

## Workflow 6: domain-classifier drift

Use this when the user asks whether a classifier can distinguish reference from analysis chunks.

```python
dc_calc = nml.DomainClassifierCalculator(
    feature_column_names=features,
    treat_as_categorical=['salary_range', 'repaid_loan_on_prev_car', 'size_of_downpayment'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
    tune_hyperparameters=False,
)
dc_results = dc_calc.fit(reference).calculate(analysis)
print(dc_results.filter(period='analysis').to_df(multilevel=False).head())
```

Domain-classifier drift uses internal LightGBM models and cross-validation. Keep hyperparameter tuning disabled for quick monitoring jobs unless the user accepts the runtime cost.

## Workflow 7: alert-count ranking

```python
univariate_one_method = results.filter(period='analysis', methods=['jensen_shannon'])
ranking = nml.AlertCountRanker().rank(univariate_one_method, only_drifting=True)
print(ranking.head())
```

The input must contain at most one categorical and one continuous drift method. For mixed feature sets, `jensen_shannon` is a convenient single method name shared by both types.

## Workflow 8: correlation ranking with performance

```python
reference, analysis, analysis_targets = nml.load_synthetic_car_loan_dataset()
analysis_with_targets = analysis.merge(analysis_targets, on='id')

# One performance metric.
performance = nml.PerformanceCalculator(
    metrics=['roc_auc'],
    y_true='repaid',
    y_pred='y_pred',
    y_pred_proba='y_pred_proba',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis_with_targets)

# One drift method per feature.
drift = nml.UnivariateDriftCalculator(
    column_names=features,
    timestamp_column_name='timestamp',
    categorical_methods=['jensen_shannon'],
    continuous_methods=['jensen_shannon'],
    chunk_size=5000,
).fit(reference).calculate(analysis)

ranker = nml.CorrelationRanker().fit(performance.filter(period='reference', metrics=['roc_auc']))
ranking = ranker.rank(
    drift.filter(period='analysis', methods=['jensen_shannon']),
    performance.filter(period='analysis', metrics=['roc_auc']),
)
```

If the ranker raises an error about multiple performance metrics or multiple drift methods, filter more narrowly.

## Workflow 9: compare drift and performance plots

```python
estimated_roc_auc = estimated_performance.filter(period='analysis', metrics=['roc_auc'])
salary_drift = univariate_drift.filter(
    period='analysis',
    column_names=['salary_range'],
    methods=['jensen_shannon'],
)
figure = estimated_roc_auc.compare(salary_drift).plot()
```

Use this to connect drift alerts to possible performance impact. For deeper performance setup, route to [../../performance-monitoring/SKILL.md](../../performance-monitoring/SKILL.md).

## Validation checklist

- Reference and analysis data contain all selected columns.
- Timestamps are available when using `chunk_period` or time-based plots.
- Categorical/continuous overrides match semantic data type.
- Custom thresholds do not rely on `chi2` support.
- Ranking inputs are filtered to one method and/or one metric.
- Target drift only runs after target labels are available.
- Multivariate drift feature lists exclude target, prediction, identifier, and period columns unless the user intentionally asks otherwise.
