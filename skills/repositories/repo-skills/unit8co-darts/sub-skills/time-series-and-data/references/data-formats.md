# TimeSeries data formats

## Mental model

A Darts `TimeSeries` stores values with axes `(time, component, sample)`:

- `time`: ordered index, either datetime-like or integer/range.
- `component`: value columns/variables in one multivariate series.
- `sample`: stochastic samples for probabilistic forecasts; deterministic series have one sample.

Do not confuse:

- **One multivariate series**: multiple components share the same time index, e.g. `sales` and `returns` for one store.
- **Multiple series**: a list of `TimeSeries`, e.g. one target series per store/item/entity for global models.

## DataFrame to one TimeSeries

```python
import pandas as pd
from darts import TimeSeries

df = pd.DataFrame({
    "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-04"]),
    "sales": [10.0, 11.0, 13.0],
    "returns": [1.0, 0.0, 2.0],
})
static_covariates = pd.DataFrame(
    {"kind": ["target", "target"], "unit": ["items", "items"]},
    index=["sales", "returns"],
)
series = TimeSeries.from_dataframe(
    df,
    time_col="timestamp",
    value_cols=["sales", "returns"],
    fill_missing_dates=True,
    freq="D",
    static_covariates=static_covariates,
)
assert series.n_components == 2
assert list(series.components) == ["sales", "returns"]
assert len(series) == 4  # 2024-01-03 was inserted
assert series.static_covariates.shape[0] in (1, series.n_components)
```

Use `fillna_value=` if inserted or existing missing values should be filled with a constant during construction. Otherwise handle missing values later with `MissingValuesFiller` in `data-processing-and-covariates`.

## From times and arrays

```python
import numpy as np
import pandas as pd
from darts import TimeSeries

times = pd.date_range("2024-01-01", periods=10, freq="D")
values = np.arange(20).reshape(10, 2)
series = TimeSeries.from_times_and_values(times, values, columns=["sales", "returns"])
assert series.values().shape == (10, 2)
```

For deterministic arrays, Darts normalizes to one sample internally. For stochastic data, use a 3D array shaped `(time, component, sample)`.

## Grouped DataFrame to multiple series

Use grouped construction when entity columns identify separate series:

```python
import pandas as pd
from darts import TimeSeries

df = pd.DataFrame({
    "store": ["A", "A", "B", "B"],
    "region": ["west", "west", "east", "east"],
    "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]),
    "sales": [10, 11, 7, 9],
    "returns": [1, 0, 0, 1],
})
series_list = TimeSeries.from_group_dataframe(
    df,
    group_cols="store",
    time_col="timestamp",
    value_cols=["sales", "returns"],
    static_cols=["region"],
    fill_missing_dates=True,
    freq="D",
)
assert len(series_list) == 2
for ts in series_list:
    assert ts.n_components == 2
```

For global forecasting models, pass a list of target series and matching lists of covariate series. Keep one covariate `TimeSeries` per target entity.

## Splits, slicing, and export

```python
train, val = series.split_before(0.8)       # proportion split
last_week = series[-7:]                     # positional slice
sales = series["sales"]                    # component slice
pdf = series.pd_dataframe()                 # one series to DataFrame
```

For grouped export patterns, rebuild a table with entity identifiers explicitly. If using Darts helpers such as `to_group_dataframe()` in the installed version, verify its output columns and static/metadata behavior before relying on it.

## Validation checklist

- Are timestamps unique and sorted?
- Is frequency inferred or explicitly supplied?
- If `fill_missing_dates=True`, did inserted points create NaNs that need filling later?
- Are value columns components of one entity or separate entities?
- Do static covariates have either one row or one row per component?
- Does downstream modeling expect a single `TimeSeries` or a list/sequence?
