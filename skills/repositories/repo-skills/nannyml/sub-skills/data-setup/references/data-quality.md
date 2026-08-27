# Data Quality and Distribution Monitors

Use these APIs when the user wants to validate tabular input quality before or alongside performance and drift monitoring.

## Calculator selection

| Goal | Use | Column type |
| --- | --- | --- |
| Missing value rate or count | `nannyml.MissingValuesCalculator` | Any selected columns |
| Categorical values unseen in reference data | `nannyml.UnseenValuesCalculator` | Categorical columns; integer columns are converted to categorical inside this calculator |
| Numeric values outside reference min/max | `nannyml.NumericalRangeCalculator` | Continuous columns only |
| Categorical distribution profile per chunk | `nannyml.CategoricalDistributionCalculator` | Categorical-like columns |
| Continuous KDE distribution profile per chunk | `nannyml.ContinuousDistributionCalculator` | Continuous columns |

Data-quality calculators support the common NannyML `fit(reference).calculate(analysis)` pattern and return result objects with `filter`, `to_df`, `plot`, and `compare` support.

## Missing values

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_data_quality_dataset()
columns = [
    'car_value',
    'salary_range',
    'debt_to_income_ratio',
    'loan_length',
    'repaid_loan_on_prev_car',
    'size_of_downpayment',
    'driver_tenure',
]

missing = nml.MissingValuesCalculator(
    column_names=columns,
    normalize=True,
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

print(missing.filter(period='analysis', column_names=['salary_range']).to_df(multilevel=False).head())
```

- `normalize=True` reports `missing_values_rate` bounded from 0 to 1.
- `normalize=False` reports `missing_values_count`.
- Default thresholding is `StandardDeviationThreshold()` learned from reference chunks.
- Missing-value checks are useful before CBPE, DLE, drift, or summary-stat workflows because many downstream monitors assume required columns exist and contain usable values.

## Unseen categorical values

```python
categorical_columns = ['salary_range', 'repaid_loan_on_prev_car', 'size_of_downpayment']

unseen = nml.UnseenValuesCalculator(
    column_names=categorical_columns,
    normalize=True,
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

print(unseen.filter(period='analysis').to_df(multilevel=False).head())
```

- `normalize=True` reports `unseen_values_rate`.
- `normalize=False` reports `unseen_values_count`.
- Default threshold is `ConstantThreshold(lower=None, upper=0)`, meaning any unseen value raises an alert by default.
- The calculator tracks values seen in the reference period and compares analysis chunks against those sets.
- `y_pred_column_name` and `y_true_column_name` can be supplied when prediction or target columns should be treated as categorical for this calculator.

## Numerical range

```python
continuous_columns = ['car_value', 'debt_to_income_ratio', 'loan_length', 'driver_tenure']

range_result = nml.NumericalRangeCalculator(
    column_names=continuous_columns,
    normalize=True,
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

print(range_result.filter(period='analysis', column_names=['car_value']).to_df(multilevel=False).head())
```

- `normalize=True` reports `out_of_range_values_rate`.
- `normalize=False` reports `out_of_range_values_count`.
- Default threshold is `ConstantThreshold(lower=None, upper=0)`, so out-of-range observations alert by default.
- The reference period establishes each selected column's `[min, max]` bounds.
- All `column_names` must be continuous; categorical columns raise `InvalidArgumentsException`.

## Distribution helpers

These calculators are descriptive distribution profilers rather than alerting drift tests.

```python
continuous_distribution = nml.ContinuousDistributionCalculator(
    column_names=['car_value', 'debt_to_income_ratio'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
    points_per_joy_plot=50,
).fit(reference).calculate(analysis)

categorical_distribution = nml.CategoricalDistributionCalculator(
    column_names=['salary_range', 'size_of_downpayment'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)
```

Use them when the user wants chunk-level distribution data or plots rather than alert thresholds. For drift alerts, route to [../../drift-monitoring/SKILL.md](../../drift-monitoring/SKILL.md).

## Result interpretation

Flat DataFrame columns will include chunk metadata plus a per-column metric such as:

- `missing_values_rate_value`
- `unseen_values_rate_value`
- `out_of_range_values_rate_value`
- `upper_threshold`
- `lower_threshold`
- `alert`
- `sampling_error` and confidence boundaries where implemented

Use filtered plots for readability:

```python
fig = missing.filter(period='analysis', column_names=['salary_range']).plot()
```

Data-quality results can be compared with performance or drift after filtering to one result key:

```python
quality_one = missing.filter(period='analysis', column_names=['salary_range'])
perf_one = estimated.filter(period='analysis', metrics=['roc_auc'])
fig = perf_one.compare(quality_one).plot()
```

## Validation checklist

- All selected `column_names` exist in reference and analysis data.
- Reference and analysis data are non-empty.
- `UnseenValuesCalculator` columns are categorical or intentionally converted to categorical.
- `NumericalRangeCalculator` columns are continuous.
- The chosen `normalize` mode matches whether the user wants rates or counts.
- Chunking and timestamp choices match related performance/drift workflows if results will be compared or ranked.
- Custom thresholds reflect rate/count units.
