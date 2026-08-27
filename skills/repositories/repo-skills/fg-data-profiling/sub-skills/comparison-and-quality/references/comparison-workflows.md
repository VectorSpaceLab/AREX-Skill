# Comparison Workflows

## When to read

Read this when a user asks to compare train/validation/test splits, different
time periods, before/after preprocessing datasets, or previously computed
profile summaries.

## Compare two reports

```python
from data_profiling import ProfileReport

before = ProfileReport(before_df, title="Before", minimal=True)
after = ProfileReport(after_df, title="After", minimal=True)
comparison = before.compare(after)
comparison.to_file("before-after-profile.html")
```

## Compare more than two reports

```python
from data_profiling import compare

comparison = compare([train_report, validation_report, test_report])
comparison.to_file("split-comparison.html")
statistics = comparison.get_description()
```

More than two reports are accepted but may produce formatting warnings. Use
short labels and `report.precision` around 8 when columns are crowded.

## Compare from computed descriptions

If individual reports have already computed summaries:

```python
descriptions = [report.get_description() for report in reports]
comparison = compare(descriptions)
```

Do not mix `ProfileReport` objects and description objects in the same call.

## Constraints and behaviors

- At least two reports are required.
- All inputs must have the same type: all `ProfileReport` or all raw
  descriptions.
- Time-series and non-time-series reports cannot be compared together.
- `ProfileReport` inputs must still have their DataFrames when comparison needs
  DataFrame-backed features.
- Different column sets warn and the comparison focuses on columns available
  from the left/base report.
- Report labels come from each report's `config.title`.

## Styling comparison output

```python
from data_profiling.config import Settings

settings = Settings()
settings.report.precision = 8
settings.html.style.primary_colors = ["#0d6efd", "#dc3545", "#198754"]
comparison = compare([a, b, c], config=settings)
```

If passing a `config` and `compute=True`, the package recomputes each report's
description using the new config where applicable.

## Safe bundled smoke

```bash
python scripts/compare_reports_smoke.py --output /tmp/comparison-smoke.html
```

The helper constructs two tiny DataFrames, compares them, writes HTML, and
asserts the comparison table contains two row counts.
