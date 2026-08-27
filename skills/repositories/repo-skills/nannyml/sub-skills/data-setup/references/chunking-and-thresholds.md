# Chunking and Thresholds

NannyML reports monitoring values by data chunks. Alert thresholds are learned from reference chunks and applied to analysis chunks.

## Chunking options

Most calculators and estimators accept one of these arguments:

- `chunk_size`: fixed number of observations per chunk.
- `chunk_number`: target number of chunks.
- `chunk_period`: pandas-style time period such as `W`, `M`, or `Q`; requires `timestamp_column_name`.
- `chunker`: explicit `Chunker` instance; use when you need custom incomplete-chunk behavior.

If no chunking option is supplied, NannyML uses `DefaultChunker`, which aims for about 10 chunks.

## Chunker API

```python
nannyml.DefaultChunker(timestamp_column_name=None)
nannyml.SizeBasedChunker(chunk_size, incomplete='keep', timestamp_column_name=None)
nannyml.CountBasedChunker(chunk_number, incomplete='keep', timestamp_column_name=None)
nannyml.PeriodBasedChunker(timestamp_column_name, offset='W')
```

`SizeBasedChunker` and `CountBasedChunker` support `incomplete`:

- `'keep'`: keep a final incomplete chunk.
- `'drop'`: drop leftover observations.
- `'append'`: append leftover observations to the last complete chunk.

`PeriodBasedChunker` groups by pandas time periods. Common offsets include:

| Alias | Meaning |
| --- | --- |
| `S` | second |
| `T` or `min` | minute |
| `H` | hour |
| `D` | day |
| `W` | week |
| `M` | month |
| `Q` | quarter |
| `A` or `Y` | year |

## Chunking examples

```python
# Fixed-size chunks.
calc = nml.UnivariateDriftCalculator(column_names=features, chunk_size=5000)

# Fixed count.
calc = nml.UnivariateDriftCalculator(column_names=features, chunk_number=10)

# Calendar-week chunks.
calc = nml.UnivariateDriftCalculator(
    column_names=features,
    timestamp_column_name='timestamp',
    chunk_period='W',
)

# Explicit incomplete behavior.
chunker = nml.SizeBasedChunker(chunk_size=5000, incomplete='append', timestamp_column_name='timestamp')
calc = nml.UnivariateDriftCalculator(column_names=features, chunker=chunker)
```

## Chunking validation rules

- `chunk_size` and `chunk_number` must be positive integers.
- Period-based chunking requires a timestamp column.
- A timestamp-aware chunker checks that the timestamp column exists.
- Very few chunks trigger a warning that the number of chunks is too low.
- Count-based chunking can produce very different chunk sizes for reference and analysis if their row counts differ.
- For comparison plots and rankers, keep chunking consistent across the results being compared.

## Threshold classes

```python
nannyml.ConstantThreshold(lower=None, upper=None)
nannyml.StandardDeviationThreshold(
    std_lower_multiplier=3,
    std_upper_multiplier=3,
    offset_from=numpy.nanmean,
)
nannyml.thresholds.calculate_threshold_values(
    threshold,
    data,
    lower_threshold_value_limit=None,
    upper_threshold_value_limit=None,
    override_using_none=False,
    logger=None,
    metric_name=None,
)
```

A `None` lower or upper value disables that side of a threshold.

## Constant thresholds

Use `ConstantThreshold` when the alert boundary is a domain rule:

```python
missing_threshold = nml.ConstantThreshold(lower=None, upper=0.02)
missing = nml.MissingValuesCalculator(column_names=['salary_range'], threshold=missing_threshold)
```

Validation rules:

- `lower` and `upper` must be `float`, `int`, or `None`; booleans and strings are invalid.
- If both are set, `lower < upper` must hold.

## Standard-deviation thresholds

Use `StandardDeviationThreshold` when alert boundaries should be based on reference chunks:

```python
threshold = nml.StandardDeviationThreshold(
    std_lower_multiplier=2,
    std_upper_multiplier=None,
)
```

Validation rules:

- Multipliers must be non-negative numbers or `None`.
- `None` disables that side.
- `offset_from` is an aggregate function such as `numpy.nanmean`, `numpy.mean`, or `numpy.median`.

## Threshold mappings

Some calculators take one threshold object, and some take mappings by metric/method.

```python
# Single-threshold calculator.
quality = nml.NumericalRangeCalculator(
    column_names=['car_value'],
    threshold=nml.ConstantThreshold(lower=None, upper=0),
)

# Metric/method threshold mapping.
thresholds = {
    'f1': nml.ConstantThreshold(lower=0.75, upper=None),
    'jensen_shannon': nml.StandardDeviationThreshold(std_lower_multiplier=None, std_upper_multiplier=2),
}
```

`UnivariateDriftCalculator` currently ignores custom thresholds for `chi2` and emits a warning. Do not rely on a custom `chi2` threshold.

## Threshold value limits

Some metrics or methods have theoretical limits, such as rates bounded between 0 and 1. NannyML clamps or overrides threshold values that exceed these limits and can log a warning. For example, a negative lower threshold may be raised to `0` for a non-negative metric.

## Selection guidance

- Use chunk sizes large enough to make metric estimates stable but small enough to detect changes early.
- Prefer time-based chunking when the user needs calendar-aligned monitoring or scheduled runs.
- Prefer size-based chunks for consistent sample counts.
- Prefer count-based chunks only when the user wants a fixed number of result points.
- Use custom thresholds when business constraints are clearer than statistical defaults.
- Keep threshold and chunking choices consistent when comparing results or ranking by correlation.
