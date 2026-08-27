# Data processing and covariate workflows

## Workflow: train-only fill and scale

```python
from darts.dataprocessing import Pipeline
from darts.dataprocessing.transformers import MissingValuesFiller, Scaler

train, val = series.split_before(0.8)
preprocess = Pipeline([MissingValuesFiller(), Scaler()])
train_clean = preprocess.fit_transform(train)
val_clean = preprocess.transform(val)

model.fit(train_clean)
forecast_scaled = model.predict(len(val_clean))
forecast = preprocess.inverse_transform(forecast_scaled, partial=True)
```

Validation points:

- `preprocess` is fit exactly once on `train`.
- `val` and future test data use `transform()`, not `fit_transform()`.
- `MissingValuesFiller` is not invertible, so `partial=True` inverse-transforms only invertible stages such as `Scaler`.
- Inverse transform is applied only with the fitted pipeline that saw the same components.
- Missing-date insertion belongs in `TimeSeries` construction; missing-value filling belongs here.

## Workflow: generated future calendar covariates

For a daily target and a 5-step forecast, create covariates that extend past the target end:

```python
import pandas as pd
from darts import TimeSeries
from darts.utils.timeseries_generation import datetime_attribute_timeseries

horizon = 5
extended_index = pd.date_range(
    series.start_time(),
    periods=len(series) + horizon,
    freq=series.freq,
)
dummy = TimeSeries.from_times_and_values(extended_index, range(len(extended_index)))
dow = datetime_attribute_timeseries(dummy, attribute="dayofweek", one_hot=False)
month = datetime_attribute_timeseries(dummy, attribute="month", one_hot=False)
future_covariates = dow.stack(month)
assert future_covariates.end_time() >= series.end_time() + horizon * series.freq
```

For business calendars or holidays, add caller-provided covariates or Darts holiday helpers when the installed package and locale support them. Keep the final covariate as a Darts `TimeSeries` with a compatible time index.

## Workflow: past and future covariates with multiple series

```python
targets = TimeSeries.from_group_dataframe(df, group_cols="store", time_col="date", value_cols="sales")
future_covs = TimeSeries.from_group_dataframe(calendar_df, group_cols="store", time_col="date", value_cols=["promo", "dow"])
assert len(targets) == len(future_covs)
for target, cov in zip(targets, future_covs):
    assert cov.freq == target.freq
    assert cov.end_time() >= target.end_time() + horizon * target.freq
```

If the group ordering is ambiguous, sort by group key before construction or attach/inspect metadata/static covariates.

## Workflow: covariate-compatible model handoff

After covariates are valid:

- For regression/global models, route to `forecasting-workflows` and map `lags`, `lags_past_covariates`, and `lags_future_covariates`.
- For neural models, route to `torch-and-foundation-models` and map `input_chunk_length`, `output_chunk_length`, and model-specific covariate support.
- If a local statistical model rejects covariate arguments, switch model family; do not force the argument.

## Workflow: inverse-transform forecast after probabilistic prediction

When a model produces stochastic samples, inverse-transform the forecast before metrics if the model was trained on scaled targets:

```python
forecast_scaled = model.predict(n=horizon, num_samples=100)
forecast = preprocess.inverse_transform(forecast_scaled, partial=True)
```

Then route quantile/interval metrics to `evaluation-and-explainability`.
