---
name: data-setup
description: "Prepare NannyML reference/analysis data, choose chunking and
  thresholds, use bundled datasets, and monitor data quality or summary
  statistics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Setup

Use this sub-skill when the task is about preparing tabular data for NannyML monitoring, choosing reference/analysis columns, configuring chunks and thresholds, selecting built-in datasets, or running data-quality and summary-statistic calculators.

Route performance estimation/calculation to `performance-monitoring`, drift detection/ranking to `drift-monitoring`, and YAML/CLI automation to `cli-and-automation`.

## Quick routing

- Read [references/data-requirements.md](references/data-requirements.md) for reference/analysis periods, timestamp, feature, prediction, probability, target, and joining rules.
- Read [references/chunking-and-thresholds.md](references/chunking-and-thresholds.md) for `chunk_size`, `chunk_number`, `chunk_period`, explicit chunkers, and custom thresholds.
- Read [references/data-quality.md](references/data-quality.md) for missing values, unseen values, numerical ranges, and distribution helper calculators.
- Read [references/summary-stats.md](references/summary-stats.md) for average, median, row count, standard deviation, and sum monitors.
- Read [references/troubleshooting.md](references/troubleshooting.md) when errors mention missing columns, categorical vs continuous restrictions, invalid chunker args, threshold ordering, too few chunks, or empty datasets.
- Read [../../references/datasets.md](../../references/datasets.md) to choose a bundled example dataset.

## Common setup path

1. Choose the data period split: reference for baseline expectations, analysis for monitored records.
2. Identify semantic columns: timestamp, model features, prediction label, prediction probability/probabilities, target labels, join keys, and any columns excluded from monitoring.
3. Pick chunking: fixed size, fixed count, period-based, or an explicit chunker.
4. Decide thresholds: defaults, constant thresholds, or standard-deviation thresholds per metric/method/calculator.
5. Run data-quality or summary-stat checks before or alongside drift/performance workflows.
6. Convert results to flat DataFrames for assertions/logs and plot only filtered views when the output is large.

## Data-quality quick examples

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_data_quality_dataset()
all_features = ['car_value', 'salary_range', 'debt_to_income_ratio', 'loan_length', 'repaid_loan_on_prev_car', 'size_of_downpayment', 'driver_tenure']

missing = nml.MissingValuesCalculator(
    column_names=all_features,
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

unseen = nml.UnseenValuesCalculator(
    column_names=['salary_range', 'repaid_loan_on_prev_car', 'size_of_downpayment'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)

range_result = nml.NumericalRangeCalculator(
    column_names=['car_value', 'debt_to_income_ratio', 'loan_length'],
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis)
```

## Chunking quick examples

```python
# Fixed-size chunks.
calc = nml.MissingValuesCalculator(column_names=all_features, chunk_size=5000)

# Fixed number of chunks.
calc = nml.MissingValuesCalculator(column_names=all_features, chunk_number=10)

# Time-period chunks require a timestamp column.
calc = nml.MissingValuesCalculator(column_names=all_features, timestamp_column_name='timestamp', chunk_period='W')

# Explicit chunker when incomplete-chunk behavior matters.
chunker = nml.SizeBasedChunker(chunk_size=5000, incomplete='append', timestamp_column_name='timestamp')
calc = nml.MissingValuesCalculator(column_names=all_features, chunker=chunker)
```

## Threshold quick examples

```python
threshold = nml.ConstantThreshold(lower=None, upper=0.02)
missing = nml.MissingValuesCalculator(column_names=['car_value'], threshold=threshold)

thresholds = {'jensen_shannon': nml.StandardDeviationThreshold(std_lower_multiplier=None, std_upper_multiplier=2)}
drift = nml.UnivariateDriftCalculator(column_names=['car_value'], continuous_methods=['jensen_shannon'], thresholds=thresholds)
```

## Decision points

- Use `MissingValuesCalculator` for NaN/missing-rate or missing-count monitoring.
- Use `UnseenValuesCalculator` only on categorical columns or columns that should be treated as categorical.
- Use `NumericalRangeCalculator` only on continuous columns.
- Use summary statistics when the user wants simple aggregate monitors rather than formal drift tests.
- Use `PeriodBasedChunker` or `chunk_period` only when a timestamp column is present and parseable.
- Use `to_df(multilevel=False)` when exporting or inspecting result columns programmatically.
- Use built-in datasets for reproducible examples rather than inventing large fixtures.

## Route elsewhere

- CBPE, DLE, realized performance, confusion matrix, or business value -> [../performance-monitoring/SKILL.md](../performance-monitoring/SKILL.md)
- Univariate/multivariate drift, output/target drift, or rankers -> [../drift-monitoring/SKILL.md](../drift-monitoring/SKILL.md)
- CLI YAML sections, config discovery, scheduling, writers, or stores -> [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md)
