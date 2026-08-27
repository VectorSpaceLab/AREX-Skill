# Operations and migration API reference

This reference lists the operational APIs most relevant to installation diagnostics, logging, reproducibility, plotting, serialization, trainer settings, and TorchProphet migration for NeuralProphet `1.0.0rc10`.

## Package entry points

| Entry point | Signature or usage | Purpose | Validation check |
| --- | --- | --- | --- |
| Module CLI | `python -m neuralprophet --version` or `python -m neuralprophet -V` | Print installed version and exit. | Exit status is 0 and output contains the version string. |
| Version constant | `neuralprophet.__version__` | Python-side package version. | Matches distribution metadata for the installed package. |
| Main model | `from neuralprophet import NeuralProphet` | Forecast model class. | Constructor accepts the operational knobs below. |
| Prophet wrapper | `from neuralprophet import TorchProphet` | Prophet-style migration wrapper over `NeuralProphet`. | Wrapper fit/predict works on `ds`, `y` data without Prophet-only features. |
| Serialization | `from neuralprophet import save, load` | Package-level model save/load helpers. | Saved model reloads and predicts with `map_location="cpu"`. |
| Runtime utilities | `set_log_level`, `set_random_seed` | Logging and reproducibility controls. | Log level changes and seeded fit completes. |

## Verified NeuralProphet operational signature facts

The installed `NeuralProphet` constructor includes these operationally important parameters:

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
    ...
)
```

Operational implications:

- Use `epochs`, `batch_size`, and `learning_rate` directly for small smoke tests instead of invoking automatic learning-rate search.
- Use `collect_metrics=False` and `fit(..., minimal=True)` for fast operational checks.
- Use `accelerator="cpu"` to force CPU or `accelerator="auto"` only when accelerator discovery is intended.
- `n_forecasts>1` without lags is automatically reduced to one forecast step; use lagged modeling when multi-step direct forecasts are required.

## Fit, predict, and future frame APIs used by operations

| Method | Distilled signature | Operational notes |
| --- | --- | --- |
| `fit` | `fit(df, freq="auto", validation_df=None, epochs=None, batch_size=None, learning_rate=None, early_stopping=False, minimal=False, metrics=None, progress="bar", checkpointing=False, deterministic=False, trainer_config=None)` | `df` must contain `ds` and `y`; `minimal=True` disables metrics/progress/checkpointing; `trainer_config` passes through to Lightning; `deterministic=True` requests deterministic trainer behavior. |
| `predict` | `predict(df, decompose=True, raw=False, auto_extend=True)` | Returns a dataframe with forecast columns such as `yhat1`; after save/load, check that expected `yhat*` columns are present. |
| `make_future_dataframe` | `make_future_dataframe(df, events_df=None, regressors_df=None, periods=None, n_historic_predictions=False)` | Use the same history dataframe shape and required event/regressor frames used during training. For operations smoke tests with no exogenous features, pass only `df` and `periods`. |
| `split_df` | `split_df(df, freq="auto", valid_p=0.2, local_split=False)` | Native helper for train/validation splits; route modeling choices to the forecasting or component sub-skills. |
| `crossvalidation_split_df` | `crossvalidation_split_df(df, freq="auto", k=5, fold_pct=0.1, fold_overlap_pct=0.5, global_model_cv_type="global-time")` | Operationally useful for preparing multiple validation folds; route metric interpretation to evaluation skills. |

## Serialization API

| API | Signature | Inputs | Returns / effects | Failure checks |
| --- | --- | --- | --- | --- |
| `save` | `save(forecaster, path)` | Fitted `NeuralProphet`; path-like object or binary buffer. | Writes Torch/Pickle model artifact. Temporarily removes trainer references and restores them after saving. | Do not overwrite user files unless explicitly requested; verify path or buffer can be written. |
| `load` | `load(path, map_location=None)` | Path-like object or binary buffer from `save`; optional Torch map location. | Returns a fitted forecaster and restores a trainer. | Use `map_location="cpu"` for CPU-only restore; load only trusted artifacts from compatible versions. |

Minimal persistence validation:

```python
save(model, model_path)
loaded = load(model_path, map_location="cpu")
forecast = loaded.predict(future)
yhat_cols = [c for c in forecast.columns if c.startswith("yhat")]
assert yhat_cols
```

## Logging and seed utilities

| API | Signature | Behavior | Use pattern |
| --- | --- | --- | --- |
| `set_random_seed` | `set_random_seed(seed: int = 0)` | Seeds NumPy, Torch, and Lightning worker seeding. | Call immediately before each `fit`. |
| `set_log_level` | `set_log_level(log_level: str = "INFO", include_handlers: bool = False)` | Sets `NP` logger level; optionally updates attached handlers. | Use `"ERROR"` for smoke scripts and `"INFO"` for normal training visibility. |

Valid log levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL` or numeric equivalents.

## Plotting APIs

| API | Signature shape | Backends | Output expectation |
| --- | --- | --- | --- |
| `set_plotting_backend` | `set_plotting_backend(plotting_backend: str)` | `plotly`, `matplotlib`, `plotly-resampler`, `plotly-static` | Sets model default for future plots. Raises `ValueError` on invalid backend. |
| `plot` | `plot(fcst, df_name=None, ax=None, xlabel="ds", ylabel="y", figsize=(10, 6), forecast_in_focus=None, plotting_backend=None)` | Same backend list. | Forecast plot over history/future. |
| `plot_latest_forecast` | Accepts forecast dataframe and backend options. | Same backend list. | Latest forecast view. |
| `plot_components` | Accepts forecast dataframe, component filters, focus options, and backend. | Same backend list. | Component plots for available fitted components. |
| `plot_parameters` | Accepts optional component, quantile, forecast focus, and backend options. | Same backend list. | Fitted parameter/component diagnostics. |

Backend selection notes:

- `plotting_backend=None` lets NeuralProphet auto-select; in notebook-like environments it may choose `plotly-resampler` if available.
- `plotly-resampler` depends on the optional `plotly-resampler` package and only works reliably in supported notebook environments.
- `plotly-static` uses Plotly static export support through Kaleido.
- `matplotlib` is the safest backend for non-interactive smoke checks.

## Accelerator and trainer knobs

| Knob | Where | Meaning | Safe operational default |
| --- | --- | --- | --- |
| `accelerator` | `NeuralProphet(..., accelerator=None)` | Lightning accelerator selection. Strings include `cpu`, `gpu`, `mps`, and `auto`. | Use `"cpu"` for deterministic smoke tests; use `None` to avoid explicit accelerator selection. |
| `trainer_config` | Constructor or `fit(..., trainer_config=None)` | Additional PyTorch Lightning `Trainer` configuration. Fit-time value updates the stored train config. | Supply only caller-owned options; use a temporary `default_root_dir` for no persistent trainer output. |
| `checkpointing` | `fit(..., checkpointing=False)` | Enables/disables Lightning model checkpointing. | Keep `False` for smoke tests and serialization checks. |
| `minimal` | `fit(..., minimal=False)` | Disables metrics, progress, and checkpointing when `True`. | Use `True` for quick operational checks. |
| `progress` | `fit(..., progress="bar")` | Progress display mode; `"plot"` requires metrics. | Use `None` in automated scripts. |
| `deterministic` | `fit(..., deterministic=False)` | Requests deterministic trainer behavior. | Use `True` with `set_random_seed` for reproducibility checks. |

## TorchProphet migration API

`TorchProphet` accepts Prophet-style arguments plus NeuralProphet `**kwargs`.

### Constructor mapping

| Prophet-style argument | TorchProphet behavior | NeuralProphet-native note |
| --- | --- | --- |
| `growth="linear"` | Passed through. | Use direct `NeuralProphet(growth="linear")` for native code. |
| `growth="flat"` | Converted to NeuralProphet `growth="off"` with a warning. | Prefer native `growth="off"` when not using the wrapper. |
| `changepoints` | Passed through. | Dates are normalized during fit. |
| `n_changepoints` | Defaults to 25 in the wrapper. | Direct NeuralProphet default is 10. |
| `changepoint_range` | Passed as `changepoints_range`. | Note the pluralized native parameter name. |
| `yearly_seasonality`, `weekly_seasonality`, `daily_seasonality` | Passed through. | Values can be `auto`, booleans, or Fourier-order-like integers. |
| `holidays` | Converted to events using unique `holiday` values plus max lower/upper windows. | Native code can use `add_events` or `add_country_holidays` explicitly. |
| `seasonality_mode` | Passed through. | `additive` and `multiplicative` are supported. |
| `interval_width` | Converted to symmetric quantiles when `quantiles` is not supplied. | Prefer explicit `quantiles` for native uncertainty workflows. |
| `seasonality_prior_scale`, `holidays_prior_scale`, `changepoint_prior_scale` | Logs unsupported regularization error. | Use `seasonality_reg`, event/holiday regularization, or `trend_reg`. |
| `mcmc_samples`, `uncertainty_samples` | Logs warning; not required by NeuralProphet. | Use quantiles/conformal workflows instead. |
| `stan_backend` | Logs warning; not used. | NeuralProphet is Torch/Lightning based, not Stan based. |

### Wrapper methods

| Method | Behavior | Unsupported or surprising behavior |
| --- | --- | --- |
| `fit(df, **kwargs)` | Calls NeuralProphet `fit`; stores `history` for future calls. | Raises `NotImplementedError` if `df` contains `cap` for logistic saturation; removes `show_progress` from kwargs. |
| `predict(df=None, **kwargs)` | Uses stored history when `df` is omitted; copies event columns to Prophet-like names. | Requires successful prior fit. |
| `make_future_dataframe(periods, freq="D", include_history=True, **kwargs)` | Builds future frame from stored history; converts monthly `freq="M"` periods to approximate days. | Provide future regressor/event frames when required by the fitted model. |
| `add_seasonality(name, period, fourier_order, prior_scale=None, mode=None, condition_name=None, **kwargs)` | Calls native custom seasonality. | `condition_name` is not supported; `prior_scale` only warns. |
| `add_regressor(name, prior_scale=None, standardize="auto", mode="additive", **kwargs)` | Adds a native future regressor with `normalize=standardize`. | The wrapper does not reliably expose Prophet regressor `mode`; prefer native `add_future_regressor` for mode control. |
| `add_country_holidays(country_name, **kwargs)` | Calls native holiday support. | Only one country-holiday configuration should be active. |
| `plot`, `plot_components` | Delegate to NeuralProphet plotting. | Prophet-only plotting arguments such as capacity or uncertainty toggles are ignored with warnings. |

## Operational bundled script contract

`scripts/save_load_smoke.py` must:

- Generate tiny synthetic daily `ds`, `y` data in memory.
- Fit on CPU by default without network access.
- Save to a temporary `.np` file unless `--output-path` is provided.
- Load with `map_location="cpu"`.
- Predict on a future dataframe and print discovered `yhat*` columns.
- Avoid persistent trainer/checkpoint artifacts during default execution.
