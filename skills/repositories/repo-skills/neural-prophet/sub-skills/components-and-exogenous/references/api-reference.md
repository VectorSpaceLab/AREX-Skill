# Components API Reference

This reference is for NeuralProphet 1.0.0rc10 component configuration. Register components before `fit`; methods such as `add_lagged_regressor`, `add_future_regressor`, `add_events`, `add_country_holidays`, and `add_seasonality` mutate the model and return it for optional chaining.

## Verified signatures

```python
NeuralProphet(
    growth="linear",
    changepoints=None,
    n_changepoints=10,
    seasonality_mode="additive",
    future_regressors_model="linear",
    n_forecasts=1,
    n_lags=0,
    learning_rate=None,
    epochs=None,
    batch_size=None,
    quantiles=None,
    collect_metrics=True,
    normalize="auto",
    accelerator=None,
    ...,
)

fit(df, freq="auto", validation_df=None, epochs=None, batch_size=None,
    learning_rate=None, early_stopping=False, minimal=False, metrics=None,
    progress="bar", checkpointing=False, deterministic=False,
    trainer_config=None)

predict(df, decompose=True, raw=False, auto_extend=True)
make_future_dataframe(df, events_df=None, regressors_df=None, periods=None,
    n_historic_predictions=False)

add_lagged_regressor(names, n_lags="auto", normalize="auto", regularization=None)
add_future_regressor(name, regularization=None, normalize="auto", mode="additive")
add_events(events, lower_window=0, upper_window=0, regularization=None, mode="additive")
add_country_holidays(country_name, lower_window=0, upper_window=0,
    regularization=None, mode="additive")
add_seasonality(name, period, fourier_order, global_local="auto", condition_name=None)
```

`save`, `load`, plotting, TorchProphet wrappers, and trainer/accelerator operations are owned by `../operations-and-migration/SKILL.md`. Evaluation, CV, conformal prediction, and metrics are owned by `../evaluation-and-uncertainty/SKILL.md`.

## Constructor component settings

| Setting | Purpose | Safe values and notes |
| --- | --- | --- |
| `growth` | Trend family. | Source validation accepts `"linear"`, `"off"`, and `"discontinuous"`; invalid values are reset to `"linear"`. Logistic/saturating growth is not a supported NeuralProphet trend path in this version. |
| `changepoints`, `n_changepoints`, `changepoints_range` | Manual or automatic trend breakpoints. | Manual changepoints should be timestamps in the training span. Automatic changepoints are placed in the early history range. |
| `trend_reg`, `trend_reg_threshold` | Trend flexibility regularization. | Larger `trend_reg` makes changepoint changes smoother/sparser. `trend_reg_threshold=True` lets NeuralProphet choose a smoothing threshold. |
| `trend_global_local`, `trend_local_reg` | Multi-series trend sharing. | Use `"global"` to share one trend; `"local"` for separate trend per `ID`. Positive `trend_local_reg` gives regularized-local/glocal behavior. |
| `yearly_seasonality`, `weekly_seasonality`, `daily_seasonality` | Built-in seasonalities. | Each can be `True`, `False`, `"auto"`, or an integer Fourier order. |
| `yearly_seasonality_glocal_mode`, `weekly_seasonality_glocal_mode`, `daily_seasonality_glocal_mode` | Per-built-in sharing override. | Use after confirming behavior in the installed version. Prefer explicit `"global"`/`"local"`; use regularization for glocal-style sharing. |
| `seasonality_mode`, `seasonality_reg` | Seasonal effect mode and shrinkage. | `"additive"` or `"multiplicative"`. Multiplicative components require target scale care. |
| `season_global_local`, `seasonality_local_reg` | Multi-series seasonality sharing. | `"global"` shares seasonalities; `"local"` learns per-ID seasonalities. Positive local regularization gives regularized-local/glocal behavior. |
| `future_regressors_model`, `future_regressors_layers` | Future regressor architecture. | `"linear"`, `"neural_nets"`, `"shared_neural_nets"`, `"shared_neural_nets_coef"`; hidden layers apply to neural variants. |
| `n_lags`, `n_forecasts`, `ar_layers`, `ar_reg` | Autoregression from the target history. | `n_lags>0` enables AR; `n_forecasts` controls multi-step forecast columns; `ar_reg` induces sparse AR weights; `ar_layers` uses a deeper AR-Net. |
| `lagged_reg_layers` | Lagged regressor architecture. | Hidden layer sizes for lagged external covariates added with `add_lagged_regressor`. |
| `normalize`, `global_normalization`, `global_time_normalization`, `unknown_data_normalization` | Scaling for single or multi-ID data. | Keep normalization decisions consistent with the data scope; predicting unseen IDs needs deliberate handling. |

## Data columns by component

| Component | Required training data | Required future/prediction data | Main failure mode |
| --- | --- | --- | --- |
| Base target | `ds`, `y`, optional `ID` | `ds`, optional `y`, optional `ID` | Duplicate `ds` within an ID or wrong frequency belongs to core forecasting. |
| Autoregression | Enough target history for `n_lags`. | History rows before forecast origin; future `y` may be missing. | Insufficient history for `max_lags`. |
| Lagged regressor | Regressor column(s) aligned with `ds`, `y`, and `ID`. | Enough regressor history before forecast origin. | Treating unknown future covariates as lagged regressors. |
| Future regressor | Registered column in fit dataframe. | `regressors_df` with all registered future regressor columns for every future period and relevant ID. | Missing regressor column or mismatched ID. |
| Custom event | `events_df` with `event`, `ds`, optional `ID`; history expanded by `create_df_with_events`. | Pass known future event schedule as `events_df` to `make_future_dataframe`. | Event name not registered or ID not present. |
| Country holidays | Supported country/list/dict registered once. | Generated internally for relevant dates. | Unsupported country/subdivision or second holiday registration call. |
| Conditional seasonality | Condition column named by `condition_name`. | Recompute/populate condition column after future frame creation. | Future rows have `None` for the condition. |
| Global/local model | `ID` column with consistent series names. | `ID` preserved; exogenous frames include matching IDs when series-specific. | Unknown IDs or accidental broadcasting. |

## Component-specific notes

### Lagged regressors

- `names` can be one string or a list.
- `n_lags="auto"` uses AR `n_lags` when AR is enabled, otherwise 1.
- `n_lags="scalar"` means one lag; `n_lags=0` or `None` raises.
- Negative regularization is invalid. `normalize="auto"` avoids normalizing binary covariates.

### Future regressors

- Use only for values known across the forecast horizon.
- `mode="additive"` adds to the forecast; `mode="multiplicative"` scales with the trend/level.
- If `periods>0`, every registered future regressor must be present in `regressors_df`.
- For multi-ID data, `regressors_df` may omit `ID` to broadcast the same values to all IDs, or include `ID` to provide per-series values.

### Events and holidays

- `add_events` accepts a string or list. `events_df["event"]` values must match registered names exactly.
- `lower_window` and `upper_window` are inclusive offsets. For daily data, `-1` is the prior day; for other frequencies, think in regularized row/frequency steps.
- `add_country_holidays` can be called only once on a model. Pass a list for multiple countries or a dictionary for subdivisions, for example `{ "US": "CA" }`.

### Custom and conditional seasonality

- Custom names cannot be `daily`, `weekly`, or `yearly`; use constructor switches for built-ins.
- `fourier_order` must be greater than 0.
- `condition_name` must name a column with numeric 0/1 or fractional weights in both train and predict frames.

## Name validation rules

Avoid names reserved by NeuralProphet or its output columns:

```text
trend, daily, weekly, yearly, events, holidays, yhat, ID, y_scaled, ds, t, y,
index, cap, floor, cap_scaled, plus each reserved name suffixed with _lower or _upper
```

A name already used for any event, holiday, seasonality, lagged regressor, or future regressor cannot be reused for another component. Prefer clear names such as `promo_event`, `promo_intensity`, `temperature_lag`, or `business_month`.
