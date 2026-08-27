# Time-series API reference

Import with:

```python
import statsmodels.tsa.api as tsa
```

Verified signatures include:

```python
tsa.ARIMA(endog, exog=None, order=(0, 0, 0), seasonal_order=(0, 0, 0, 0),
          trend=None, enforce_stationarity=True, enforce_invertibility=True,
          concentrate_scale=False, trend_offset=1, dates=None, freq=None,
          missing='none', validate_specification=True, validate_exog=True)

tsa.SARIMAX(endog, exog=None, order=(1, 0, 0), seasonal_order=(0, 0, 0, 0),
            trend=None, measurement_error=False, time_varying_regression=False,
            mle_regression=True, simple_differencing=False,
            enforce_stationarity=True, enforce_invertibility=True,
            hamilton_representation=False, concentrate_scale=False,
            trend_offset=1, use_exact_diffuse=False, dates=None, freq=None,
            missing='none', validate_specification=True, validate_exog=True, **kwargs)
```

## Common surfaces

| API | Use |
| --- | --- |
| `acf`, `pacf`, `ccf`, `adfuller`, `kpss`, `coint`, `q_stat`, `bds` | Time-series statistics and tests. |
| `AutoReg`, `ARIMA`, `SARIMAX`, `ARDL`, `UECM` | Univariate dynamic models. |
| `ExponentialSmoothing`, `Holt`, `SimpleExpSmoothing`, `ETSModel`, `ThetaModel` | Smoothing/forecasting models. |
| `STL`, `MSTL`, `seasonal_decompose`, `STLForecast` | Decomposition and decomposition-based forecasting. |
| `VAR`, `SVAR`, `VECM`, `VARMAX` | Multivariate time-series models. |
| `DynamicFactor`, `DynamicFactorMQ`, `UnobservedComponents` | State-space/factor/structural models. |
| `bkfilter`, `cffilter`, `hpfilter`, `hamilton_filter` | Filters. |
| `x13_arima_analysis`, `x13_arima_select_order` | External X-13/X-12 binary wrapper. |

## Result methods

Common result methods include `summary()`, `forecast(steps=...)`, `get_forecast(steps=...)`, `predict(...)`, `plot_diagnostics()` for some state-space results, `resid`, `aic`, `bic`, and model-specific roots or stationarity diagnostics. Always check whether a method exists on the fitted result class.
