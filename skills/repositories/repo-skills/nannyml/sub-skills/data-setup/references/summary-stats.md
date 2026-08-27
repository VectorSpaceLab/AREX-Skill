# Summary Statistics

Use NannyML summary-stat calculators when the user wants simple chunk-level monitors such as row count, averages, medians, standard deviations, or sums rather than formal drift tests.

## Calculator selection

| Goal | Use | Column requirement | Metric key |
| --- | --- | --- | --- |
| Average per chunk | `nannyml.SummaryStatsAvgCalculator` | Continuous columns | `values_avg` |
| Median per chunk | `nannyml.SummaryStatsMedianCalculator` | Continuous columns | `values_median` |
| Row count per chunk | `nannyml.SummaryStatsRowCountCalculator` | No `column_names` argument | `rows_count` |
| Standard deviation per chunk | `nannyml.SummaryStatsStdCalculator` | Continuous columns | `values_std` |
| Sum per chunk | `nannyml.SummaryStatsSumCalculator` | Continuous columns | `values_sum` |

All summary-stat calculators support the common NannyML pattern:

```python
calculator = calculator.fit(reference_df)
result = calculator.calculate(analysis_df)
```

Default thresholding is `StandardDeviationThreshold()` learned from reference chunks unless you pass a custom `threshold`.

## Continuous summary-stat workflow

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_price_dataset()
continuous_features = ['car_age', 'km_driven', 'price_new', 'accident_count', 'door_count']

avg = nml.SummaryStatsAvgCalculator(
    column_names=continuous_features,
    timestamp_column_name='timestamp',
    chunk_size=6000,
).fit(reference).calculate(analysis)

median = nml.SummaryStatsMedianCalculator(
    column_names=continuous_features,
    timestamp_column_name='timestamp',
    chunk_size=6000,
).fit(reference).calculate(analysis)

std = nml.SummaryStatsStdCalculator(
    column_names=continuous_features,
    timestamp_column_name='timestamp',
    chunk_size=6000,
).fit(reference).calculate(analysis)

sum_result = nml.SummaryStatsSumCalculator(
    column_names=['km_driven'],
    timestamp_column_name='timestamp',
    chunk_size=6000,
).fit(reference).calculate(analysis)

print(avg.filter(period='analysis', column_names=['km_driven']).to_df(multilevel=False).head())
```

## Row-count workflow

Row count monitors chunk population and does not take `column_names`.

```python
row_count = nml.SummaryStatsRowCountCalculator(
    timestamp_column_name='timestamp',
    chunk_size=6000,
).fit(reference).calculate(analysis)

print(row_count.filter(period='analysis').to_df(multilevel=False).head())
```

Use row-count alerts to detect ingestion delays, missing batches, unexpected batch-size changes, or scheduled monitoring jobs that ran against partial data.

## Custom thresholds

```python
threshold = nml.ConstantThreshold(lower=1000, upper=None)
row_count = nml.SummaryStatsRowCountCalculator(threshold=threshold, chunk_size=5000)

std_threshold = nml.StandardDeviationThreshold(std_lower_multiplier=None, std_upper_multiplier=2)
std = nml.SummaryStatsStdCalculator(column_names=['price_new'], threshold=std_threshold)
```

Use constant thresholds when the expected business boundary is known, and standard-deviation thresholds when the reference baseline should define alert limits.

## Result usage

For a single-column stat result:

```python
one_column = avg.filter(period='analysis', column_names=['km_driven'])
flat = one_column.to_df(multilevel=False)
fig = one_column.plot()
```

For row count:

```python
flat = row_count.filter(period='analysis').to_df(multilevel=False)
fig = row_count.filter(period='analysis').plot()
```

Summary-stat results can be compared with performance or drift after filtering to one key:

```python
perf = estimated.filter(period='analysis', metrics=['rmse'])
stat = avg.filter(period='analysis', column_names=['km_driven'])
fig = perf.compare(stat).plot()
```

## Data-type constraints

Average, median, standard deviation, and sum split selected columns by pandas dtype and reject categorical columns. Categorical dtypes are object, string, category, and bool. Continuous dtypes include int, unsigned int, and float types.

If a column is semantically categorical but stored as integer, do not include it in continuous summary-stat calculators unless a numeric aggregate is meaningful. Cast it to `category` and use categorical distribution, unseen values, or univariate categorical drift instead.

## When to choose summary stats vs drift

Use summary stats when the user asks for:

- mean/median/std/sum/row count over time;
- simple monitoring dashboards;
- ingestion-volume checks;
- business thresholds on an aggregate column;
- a lightweight signal before a more formal drift analysis.

Use [../../drift-monitoring/SKILL.md](../../drift-monitoring/SKILL.md) when the user asks for statistical drift tests, feature-distribution changes, or feature ranking.

## Validation checklist

- Continuous summary-stat columns exist in reference and analysis data.
- Categorical columns are excluded from avg/median/std/sum.
- Row-count calculators do not receive `column_names`.
- Chunking is stable enough for the chosen aggregate.
- Threshold units match the statistic being monitored.
- Result comparisons are filtered to one key per side.
