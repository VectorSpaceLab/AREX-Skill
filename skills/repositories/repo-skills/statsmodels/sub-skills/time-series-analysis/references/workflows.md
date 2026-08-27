# Time-series workflows

## Stationarity and autocorrelation checks

```python
import pandas as pd
import statsmodels.tsa.api as tsa

series = pd.Series(values, index=pd.date_range("2020-01-01", periods=len(values), freq="M"))
adf_stat, adf_pvalue, *_ = tsa.adfuller(series.dropna())
acf_values = tsa.acf(series.dropna(), nlags=12)
```

ADF and KPSS have different null hypotheses. Use both only when the interpretation is stated clearly.

## ARIMA/SARIMAX forecast

```python
from statsmodels.tsa.arima.model import ARIMA

model = ARIMA(series, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), missing="raise")
res = model.fit()
forecast = res.get_forecast(steps=6).summary_frame()
```

Use `SARIMAX` when you need seasonal structure, exogenous regressors, or deeper state-space controls. If fitted with `exog`, future forecasts require future `exog` with matching shape.

## STL decomposition and smoothing

```python
from statsmodels.tsa.seasonal import STL

stl = STL(series, period=12, robust=True).fit()
trend = stl.trend
seasonal = stl.seasonal
```

`period` must match the seasonal cycle. When the index has no frequency, provide `period` explicitly.

## VAR/VECM

```python
from statsmodels.tsa.vector_ar.var_model import VAR

res = VAR(df[["y1", "y2"]]).fit(maxlags=2, ic="aic")
forecast = res.forecast(df[["y1", "y2"]].values[-res.k_ar:], steps=4)
```

VAR workflows require aligned multivariate observations and enough rows for lag order. VECM requires cointegration assumptions and deterministic-term choices.

## X-13/X-12 optional workflow

X-13/X-12 functions are wrappers around external executables. A package import check does not prove the binary exists. If unavailable, report the optional block and provide non-X13 alternatives such as STL or SARIMAX when suitable.
