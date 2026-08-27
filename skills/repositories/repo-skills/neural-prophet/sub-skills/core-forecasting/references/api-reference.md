# Core API Reference

## Verified signatures

The following signatures were verified from an installed NeuralProphet `1.0.0rc10` package.

```python
NeuralProphet(
    growth='linear', changepoints=None, n_changepoints=10,
    changepoints_range=0.8, trend_reg=0, trend_reg_threshold=False,
    yearly_seasonality='auto', weekly_seasonality='auto', daily_seasonality='auto',
    seasonality_mode='additive', future_regressors_model='linear',
    n_forecasts=1, n_lags=0, learning_rate=None, epochs=None,
    batch_size=None, quantiles=None, collect_metrics=True,
    normalize='auto', accelerator=None, trainer_config=None, ...)

NeuralProphet.fit(
    self, df, freq='auto', validation_df=None, epochs=None,
    batch_size=None, learning_rate=None, early_stopping=False,
    minimal=False, metrics=None, metrics_log_dir=None, progress='bar',
    checkpointing=False, num_workers=0, deterministic=False,
    scheduler=None, scheduler_args=None, trainer_config=None)

NeuralProphet.predict(self, df, decompose=True, raw=False, auto_extend=True)

NeuralProphet.make_future_dataframe(
    self, df, events_df=None, regressors_df=None,
    periods=None, n_historic_predictions=False)
```

## Constructor settings most relevant to core runs

| Setting | Use |
| --- | --- |
| `n_forecasts` | Number of forecast horizons per prediction origin. Produces `yhat1...yhatN`. |
| `n_lags` | Autoregressive history length. Requires enough history before prediction rows. |
| `epochs`, `batch_size`, `learning_rate` | Let NeuralProphet auto-select for real runs, but set tiny explicit values for smoke tests. |
| `collect_metrics` | Enables training metrics; when disabled, `fit` can return `None`. |
| `normalize` | Data normalization strategy: `auto`, `soft`, `soft1`, `minmax`, `standardize`, or `off`. |
| `accelerator` | Pass `"cpu"` for deterministic CPU checks; optional GPU use belongs to operations guidance. |

## Data utility helpers

These helper signatures are useful when validating data before model calls:

```python
df_utils.check_dataframe(df, check_y=True, covariates=None,
                         regressors=None, events=None,
                         seasonalities=None, future=None)

df_utils.infer_frequency(df, freq, n_lags, min_freq_percentage=0.7)

df_utils.split_df(df, n_lags, n_forecasts, valid_p=0.2,
                  inputs_overbleed=True, local_split=False)
```

For normal users prefer the `NeuralProphet` instance methods (`split_df`, `make_future_dataframe`) unless you are writing validation tooling.

## Output columns

Core prediction columns:

- `ds`: forecast timestamp.
- `y`: observed target when available.
- `yhat1`, `yhat2`, ...: forecast horizon columns.
- Component columns: included when `decompose=True` and relevant components are active.

Use `predict(..., raw=True)` only when you want raw forecast-origin arrays rather than the usual target-time dataframe.
