# Metrics reference

## Jensen-Shannon divergence

Import:

```python
from sdgx.metrics.column.jsd import JSD
```

Usage:

```python
score = JSD.calculate(real_df, synthetic_df, cols=["workclass"], discrete=True)
assert 0 <= score <= 1
```

Notes:

- For discrete columns, SDGX groups by the selected columns and aligns empirical probabilities.
- For continuous columns, SDGX uses Gaussian KDE and a grid of 100 points per selected variable; do not use many continuous columns at once because grid cost grows quickly.
- Identical discrete distributions should produce a score close to `0`.
- The implementation checks output bounds `[0, 1]`.

## Mutual-information similarity

Import:

```python
from sdgx.metrics.pair_column.mi_sim import MISim
```

Usage:

```python
metadata = {"feature_x": "numerical", "feature_y": "numerical"}
score = MISim.calculate(real_df["feature_x"], synthetic_df["feature_y"], metadata)
assert 0 <= score <= 1
```

`metadata` values expected by this metric are `"numerical"`, `"category"`, or `"datetime"`; these are metric-local labels, not necessarily the same as `Metadata.get_column_data_type` output. Convert SDGX metadata types when needed:

```python
def metric_type(sdgx_type: str) -> str:
    if sdgx_type in {"int", "float", "id"}:
        return "numerical"
    if sdgx_type == "datetime":
        return "datetime"
    return "category"
```

## Validation beyond metrics

Always pair metrics with structural checks:

```python
assert synthetic_df.columns.tolist() == real_df.columns.tolist()
assert len(synthetic_df) == requested_count
assert set(synthetic_df.columns) >= set(required_columns)
```

For PII/generator workflows, check that replacement columns are present and look like expected fake values, while avoiding privacy claims not proven by metrics.
