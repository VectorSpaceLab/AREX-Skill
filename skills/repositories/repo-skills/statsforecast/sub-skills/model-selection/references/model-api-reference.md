# Model API reference

This page covers the direct y-array API on individual StatsForecast model objects.
Use core-forecasting for panel DataFrame orchestration, `X_df`, persistence, and cross-validation.

## Common direct-call pattern

```python
from statsforecast.models import AutoARIMA
from statsforecast.utils import ConformalIntervals

model = AutoARIMA(
    season_length=12,
    prediction_intervals=ConformalIntervals(h=12, n_windows=2),
)
model.fit(y, X=X)
forecast = model.predict(h=12, X=X_future, level=[80, 95])
one_shot = model.forecast(y, h=12, X=X, X_future=X_future, fitted=True, level=[80, 95])
in_sample = model.predict_in_sample(level=[80, 95])
```

## Method surfaces

### `fit(y, X=None)`
- Fits the model on a single series.
- Most models accept a 1D numeric `y` array and optional `X`.
- `SklearnModel` and `UCM` are explicitly exogenous-aware.
- `AutoMFLES` and `SklearnModel` require `scikit-learn`.

### `predict(h, X=None, level=None)`
- Use after `fit` when you want the fitted object to produce a forecast.
- For exogenous-aware models, pass one future row per horizon step.
- `SklearnModel` uses `X` for the forecast rows; `h` is mainly interface consistency.

### `forecast(y, h, X=None, X_future=None, level=None, fitted=False)`
- Memory-efficient one-shot form.
- Re-fits from raw `y` instead of relying on previously stored state.
- Use this when you want a stateless forecast or when you do not want to persist the fitted object.

### `forward(y, h, X=None, X_future=None, level=None, fitted=False)`
- Present on many statistical models.
- Best read as “apply the fitted logic to an updated series”.
- Use it when a model exposes both `predict` and `forecast` but you want the object-oriented form of the one-shot computation.

### `predict_in_sample(level=None)`
- Returns fitted values when implemented.
- Often yields `fitted` plus optional `fitted-lo-*` / `fitted-hi-*` keys.
- Some models, such as `WindowAverage` and `SeasonalWindowAverage`, do not implement this method.

### `simulate(...)`
- Available on many probabilistic models.
- Use it when you need sampled future paths rather than only point forecasts.
- The exact simulation payload can vary slightly by model family, but it is always a direct model-level operation.

## Return keys

Common direct-model outputs use the same conventions:

- `mean` — point forecast
- `fitted` — in-sample fitted values when requested or supported
- `lo-<level>` / `hi-<level>` — forecast intervals
- `fitted-lo-<level>` / `fitted-hi-<level>` — fitted-value intervals when supported
- `sigma2` — conditional variance output for GARCH-style forecasts

## Special cases

### Exogenous-aware models
These classes genuinely consume exogenous regressors:
- `AutoARIMA`
- `ARIMA`
- `AutoRegressive`
- `AutoMFLES`
- `SklearnModel`
- `UCM`

If you pick one of these, keep the training and future exogenous matrices aligned with the same columns and row order.

### `SklearnModel`
- Constructor: `SklearnModel(model, prediction_intervals=None, alias=None)`.
- Wraps any scikit-learn regressor.
- `fit(y, X)` trains the wrapped estimator on `X -> y`.
- `forecast(y, h, X, X_future, ...)` and `forward(...)` both require `X_future` with one row per forecast step.
- This wrapper is ideal when the model selection question is “which classical regressor should I embed?” rather than “which statistical model should I use?”.

### `ConstantModel`, `ZeroModel`, `NaNModel`
- `ConstantModel(constant, alias='ConstantModel')` returns exact constant forecasts.
- `ZeroModel(alias='ZeroModel')` is `ConstantModel(0)`.
- `NaNModel(alias='NaNModel')` is `ConstantModel(np.nan)`.
- Their interval output is degenerate and equal to the constant value or NaN.
- They are useful as fallback models when a primary model is expected to fail or when you need an explicit sentinel.

### `WindowAverage` and `SeasonalWindowAverage`
- Both rely on a trailing history window.
- They can return NaN if the series is shorter than the configured window.
- They are conformal-interval-only models: pass `prediction_intervals=ConformalIntervals(...)` when you want interval output.

### `GARCH` and `ARCH`
- `GARCH(p, q, ...)` forecasts the mean and conditional variance `sigma2`.
- `ARCH(p, ...)` is the `q=0` special case.
- Clean, finite input matters; nonfinite observations or invalid variance recursion can break fitting.

### `UCM`
- The structural time-series wrapper uses statsmodels-style components rather than the StatsForecast conformal machinery.
- Use its component arguments (`level`, `trend`, `seasonal`, `cycle`, `autoregressive`, etc.) to express the model structure directly.

## Alias semantics
- The model name is the `alias` or, when omitted, `repr(model)`.
- Use `alias` to disambiguate duplicate classes or repeated model variants in the same ensemble.
- Useful defaults to remember: `RWD`, `SES`, `SESOpt`, `SeasESOpt`, `SeasWA`.

## Optional dependency notes
- `scikit-learn` is required for `AutoMFLES` and `SklearnModel`.
- `AutoMFLES` checks for `scikit-learn` at construction time.
- `SklearnModel` imports `sklearn.base.clone` when fitting or forecasting.
- `prophet` is only needed for the optional `AutoARIMAProphet` adapter in `statsforecast.adapters.prophet`.
