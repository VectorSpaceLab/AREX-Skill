# Results, Filtering, Plotting, and Comparisons

Use this reference for behavior shared by NannyML calculators and estimators after `fit` plus `calculate` or `estimate` has produced a `Result` object.

## Result object contract

NannyML usually returns a result object rather than a bare DataFrame. Important shared methods and properties are:

- `result.to_df(multilevel=True)`: returns a pandas DataFrame. The default keeps a multi-level column index.
- `result.to_df(multilevel=False)`: returns a flattened DataFrame that is easier to write to CSV, inspect, or assert on.
- `result.filter(...)`: returns a new result object narrowed by period, metrics, methods, or columns depending on result type.
- `result.plot(...)`: returns a Plotly figure object.
- `result.compare(other_result).plot()`: plots two single-key result objects together.
- `result.keys()`: returns key objects describing available metrics, methods, or columns.
- `result.empty`: tells writers and rankers whether there is data to use.

Most result DataFrames include chunk metadata under a `chunk` column group:

- `key`
- `chunk_index`
- `start_index`
- `end_index`
- `start_date` / `end_date` when timestamps are available
- `period` (`reference` or `analysis`)

Metric-like outputs commonly include:

- `value`
- `sampling_error` when available
- `upper_confidence_boundary` / `lower_confidence_boundary` when available
- `upper_threshold` / `lower_threshold`
- `alert`

## Filtering patterns

Performance results filter by period and metrics:

```python
# Estimated or realized performance for one metric in analysis chunks
metric_result = performance_result.filter(period='analysis', metrics=['roc_auc'])
metric_df = metric_result.to_df(multilevel=False)
```

Univariate drift results filter by period, column names, and methods:

```python
drift_result = drift_result.filter(
    period='analysis',
    column_names=['salary_range'],
    methods=['jensen_shannon'],
)
drift_df = drift_result.to_df(multilevel=False)
```

Data-quality and summary-statistic results filter by period and column names:

```python
missing_df = missing_result.filter(period='analysis', column_names=['car_value']).to_df(multilevel=False)
```

When a downstream function requires one metric or method, filter before calling it. This matters for `compare` and `CorrelationRanker`.

## Plotting patterns

Every major workflow returns Plotly figures:

```python
figure = result.filter(period='analysis').plot()
figure.show()
# Optional static export when Plotly/Kaleido is available:
# figure.write_image('monitoring-result.png')
```

Univariate drift supports two plot kinds:

```python
# Drift score / p-value over chunks
figure = univariate_result.filter(column_names=['car_value'], methods=['jensen_shannon']).plot(kind='drift')

# Distribution view for one or more columns
figure = univariate_result.filter(period='analysis', column_names=['salary_range']).plot(kind='distribution')
```

Performance, multivariate drift, data-quality, and summary-statistic results use their default plot kind. Passing an unknown plot kind raises `InvalidArgumentsException`.

## Comparing results

Use `compare` only after both sides have been filtered down to a single key. A key is usually one metric, one drift method on one column, or one data-quality/stat column.

```python
estimated_roc_auc = estimated_performance.filter(period='all', metrics=['roc_auc'])
realized_roc_auc = realized_performance.filter(period='all', metrics=['roc_auc'])
figure = estimated_roc_auc.compare(realized_roc_auc).plot()
```

Compare performance with drift or data quality by narrowing both sides:

```python
perf = estimated_performance.filter(period='analysis', metrics=['roc_auc'])
drift = univariate_drift.filter(
    period='analysis',
    column_names=['salary_range'],
    methods=['jensen_shannon'],
)
figure = perf.compare(drift).plot()
```

If a comparison error says multiple metrics are being compared, filter more narrowly.

## Exporting result data

Use writers from `nannyml.io` when you need persisted result artifacts:

```python
import nannyml as nml

writer = nml.RawFilesWriter(path='out')
writer.write(result, filename='univariate-drift.parquet', format='parquet')

pickle_writer = nml.PickleFileWriter(path='out')
pickle_writer.write(result, filename='univariate-drift.pkl')
```

`RawFilesWriter` supports `format='parquet'` and `format='csv'`. Both raw and pickle writers require a `filename` argument at write time. The database writer is optional and requires `pip install 'nannyml[db]'` before importing `nml.DatabaseWriter`.

For automated runs and calculator persistence, use [../sub-skills/cli-and-automation/references/io-and-store.md](../sub-skills/cli-and-automation/references/io-and-store.md).

## Common mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `compare` refuses to run | One or both results contain multiple keys | Filter each result to one metric/method/column first. |
| Hard-to-read DataFrame columns | Multi-level columns are enabled | Call `to_df(multilevel=False)` for flattened columns. |
| Plot has chunk index rather than timestamps | No timestamp column or no timestamp-aware chunker | Provide `timestamp_column_name` or a chunker with a timestamp column. |
| Writer says `missing required parameter 'filename'` | `RawFilesWriter` or `PickleFileWriter` was called without `filename` | Pass `filename='name.csv'`, `.parquet`, or `.pkl` according to the writer. |
| Database writer import fails | Optional `db` extra is missing | Install `nannyml[db]` and configure a SQLAlchemy-compatible connection string. |
