# TimeSeries API reference

## Key constructor signatures verified for Darts 0.46.1

```text
TimeSeries.from_dataframe(
    df,
    time_col: str | None = None,
    value_cols: list[str] | str | None = None,
    fill_missing_dates: bool | None = False,
    freq: str | int | None = None,
    fillna_value: float | None = None,
    static_covariates: pandas.Series | pandas.DataFrame | None = None,
    hierarchy: dict | None = None,
    metadata: dict | None = None,
    copy: bool = True,
)

TimeSeries.from_group_dataframe(
    df,
    group_cols: list[str] | str,
    time_col: str | None = None,
    value_cols: list[str] | str | None = None,
    static_cols: list[str] | str | None = None,
    metadata_cols: list[str] | str | None = None,
    fill_missing_dates: bool | None = False,
    freq: str | int | None = None,
    fillna_value: float | None = None,
    drop_group_cols: list[str] | str | None = None,
    n_jobs: int | None = 1,
    verbose: bool | None = False,
    copy: bool = True,
) -> list[TimeSeries]
```

## Constructor selection

| Input | Prefer | Notes |
| --- | --- | --- |
| pandas DataFrame with time column | `TimeSeries.from_dataframe()` | Supply `time_col`, `value_cols`, explicit `freq` when gaps/irregularity exist. |
| pandas Series with index | `TimeSeries.from_series()` | Good for univariate deterministic series. |
| arrays plus known time index | `TimeSeries.from_times_and_values()` | Use 2D deterministic values or 3D stochastic values. |
| table with entity/group columns | `TimeSeries.from_group_dataframe()` | Returns a list of `TimeSeries`; useful for global models. |
| xarray data | `TimeSeries.from_xarray()` | Ensure dims/coords map to Darts' time/component/sample semantics. |

## Shape and property probes

```python
print(len(series))
print(series.start_time(), series.end_time(), series.freq)
print(series.n_components, list(series.components))
print(series.n_samples, series.is_deterministic, series.is_stochastic)
print(series.static_covariates)
print(series.metadata)
```

`series.values()` returns deterministic values without the sample axis. Use `series.all_values()` when you need the full internal sample dimension.

## Static covariates

- Global static covariates: one row applies to all components.
- Component-specific static covariates: one row per component; align the index with component names when possible.
- Many global forecasting models can use static covariates; always keep static covariates attached to the target series before splitting or model fitting.

## Multiple series

Global models may consume `Sequence[TimeSeries]`. When a user has several entities:

```python
targets = TimeSeries.from_group_dataframe(df, group_cols="store", time_col="date", value_cols="sales", static_cols=["region"])
past_covariates = TimeSeries.from_group_dataframe(cov_df, group_cols="store", time_col="date", value_cols=["promo_lag"])
```

Validate that the two lists are the same length and ordered by the same grouping convention before fitting a global model.
