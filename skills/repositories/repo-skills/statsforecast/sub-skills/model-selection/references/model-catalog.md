# StatsForecast model catalog

This reference helps choose a StatsForecast model class and remember the most important constructor knobs.
It covers direct model objects only; panel orchestration, `X_df`, and multi-series batching belong to core-forecasting.

## Fast selection guide

| Need | Start with | Why |
| --- | --- | --- |
| Strong default automatic search | AutoARIMA, AutoETS, AutoTheta | Broad automatic statistical coverage with interval support |
| More aggressive multi-parameter automatic tuning | AutoMFLES, AutoTBATS | Search-heavy models for seasonal or multi-seasonal data |
| Manual ARIMA or explicit lag structure | ARIMA, AutoRegressive | You control the order or lag set directly |
| Simple trend / seasonality smoothing | SimpleExponentialSmoothing, SeasonalExponentialSmoothing, Holt, HoltWinters | Small, interpretable smoothers |
| Baseline comparison | Naive, SeasonalNaive, HistoricAverage, RandomWalkWithDrift, WindowAverage, SeasonalWindowAverage | Cheap references for model comparison |
| Sparse or intermittent demand | ADIDA, CrostonClassic, CrostonOptimized, CrostonSBA, IMAPA, TSB | Designed for zero-heavy series |
| Multiple seasonalities | MSTL, MFLES, TBATS | Multiple seasonal patterns and low-frequency signals |
| Volatility / finance | GARCH, ARCH | Conditional variance modeling |
| Learned regressors | SklearnModel | Wrap any scikit-learn estimator |
| Safe fallback | ConstantModel, ZeroModel, NaNModel | Degenerate fallback models for failures or guard rails |

## Constructor highlights by family

### Automatic forecasting
Automatic models search over statistical structure and are a good first pass for unknown series.
AutoARIMA and AutoMFLES are exogenous-aware; AutoTBATS uses native level intervals instead of the conformal constructor knob.
Simulation support differs by class, so check the direct API reference or the bundled catalog script before relying on sampled future paths.

- **AutoARIMA** — `d`, `D`, search bounds (`max_p`, `max_q`, `max_P`, `max_Q`, `max_order`, `max_d`, `max_D`), `season_length`, `distribution`, `alias`, `prediction_intervals`. Use when you want the standard automatic ARIMA search; `uses_exog=True`.
- **AutoETS** — `season_length`, `model='ZZZ'`, `damped`, `phi`, `distribution`, `alias`, `prediction_intervals`. Use when you want automatic exponential smoothing state selection.
- **AutoCES** — `season_length`, `model='Z'`, `distribution`, `alias`, `prediction_intervals`. Use for automatic complex exponential smoothing.
- **AutoTheta** — `season_length`, `decomposition_type='multiplicative'`, `model`, `distribution`, `alias`, `prediction_intervals`. Use when the theta family is the right automatic choice.
- **AutoMFLES** — `test_size`, `season_length`, `n_windows`, `config`, `step_size`, `metric`, `verbose`, `alias`, `prediction_intervals`. Use for automatic MFLES search with cross-validation; `uses_exog=True` and `scikit-learn` is required.
- **AutoTBATS** — `season_length` as an int or list, `use_boxcox`, `bc_lower_bound`, `bc_upper_bound`, `use_trend`, `use_damped_trend`, `use_arma_errors`, `alias`. Use for automatic TBATS selection on complex seasonal data.

### ARIMA family
Use these when you know the order or lag structure, or when you want a direct ARIMA-style model with exogenous regressors.
Both classes are exogenous-aware and support the direct array API.

- **ARIMA** — `order`, `season_length`, `seasonal_order`, `include_mean`, `include_drift`, `include_constant`, `method`, `fixed`, `distribution`, `alias`, `prediction_intervals`. Use when you want a manual ARIMA specification with forecast and confidence support; `uses_exog=True`.
- **AutoRegressive** — `lags`, `include_mean`, `include_drift`, `method`, `fixed`, `alias`, `prediction_intervals`. Use when a hand-picked lag structure is easier than a full ARIMA order search; `uses_exog=True`.

### Exponential smoothing
Use these for simple level, trend, or seasonal smoothing workflows.
They are fast, interpretable, and usually good baselines for series with smooth structure.

- **SimpleExponentialSmoothing** — `alpha`, `alias='SES'`, `prediction_intervals`. Use for level-only smoothing.
- **SimpleExponentialSmoothingOptimized** — `alias='SESOpt'`, `prediction_intervals`. Use when you want the model to pick the smoothing strength.
- **SeasonalExponentialSmoothing** — `season_length`, `alpha`, `alias='SeasonalES'`, `prediction_intervals`. Use for seasonal smoothing with a fixed alpha.
- **SeasonalExponentialSmoothingOptimized** — `season_length`, `alias='SeasESOpt'`, `prediction_intervals`. Use when you want seasonal smoothing with automatic tuning.
- **Holt** — `season_length`, `error_type='A'`, `alias='Holt'`, `prediction_intervals`. Use for trend-only smoothing.
- **HoltWinters** — `season_length`, `error_type='A'`, `alias='HoltWinters'`, `prediction_intervals`. Use for trend plus seasonality.

### Baseline models
Use these when you want cheap reference forecasts, sanity checks, or a fallback model.
Most support simulation and interval output; `ConstantModel`, `ZeroModel`, and `NaNModel` are exact degenerate fallbacks.

- **HistoricAverage** — `alias='HistoricAverage'`, `prediction_intervals`. Use as the mean-of-history baseline.
- **Naive** — `alias='Naive'`, `prediction_intervals`. Use as the last-value baseline.
- **RandomWalkWithDrift** — `alias='RWD'`, `prediction_intervals`. Use when a random walk with drift is a better baseline than plain naive.
- **SeasonalNaive** — `season_length`, `alias='SeasonalNaive'`, `prediction_intervals`. Use when the last seasonal cycle is the baseline.
- **WindowAverage** — `window_size`, `alias='WindowAverage'`, `prediction_intervals`. Use for a rolling average of the last `window_size` points; returns NaN if history is too short.
- **SeasonalWindowAverage** — `season_length`, `window_size`, `alias='SeasWA'`, `prediction_intervals`. Use for an average over the same seasonal positions across recent windows; returns NaN if history is too short.

### Sparse or intermittent demand
Use these when the series is mostly zeros or has sporadic non-zero bursts.
They are usually better than generic ARIMA or smoothing models on intermittent demand.

- **ADIDA** — `alias='ADIDA'`, `prediction_intervals`. Use for aggregate-disaggregate intermittent demand.
- **CrostonClassic** — `alias='CrostonClassic'`, `prediction_intervals`. Use for the classic Croston method.
- **CrostonOptimized** — `alias='CrostonOptimized'`, `prediction_intervals`. Use for the optimized Croston variant.
- **CrostonSBA** — `alias='CrostonSBA'`, `prediction_intervals`. Use for the Syntetos-Boylan approximation.
- **IMAPA** — `alias='IMAPA'`, `prediction_intervals`. Use for intermittent multiple aggregation prediction.
- **TSB** — `alpha_d`, `alpha_p`, `alias='TSB'`, `prediction_intervals`. Use when demand occurrence and demand size need separate smoothing.

### Multiple seasonalities
Use these for series with more than one clear seasonal pattern, such as daily plus weekly hourly data.
If you need decomposition features rather than the model itself, route that work to feature-engineering.

- **MSTL** — `season_length` as an int or list, `trend_forecaster=AutoETS(model='ZZN')`, `stl_kwargs`, `alias='MSTL'`, `prediction_intervals`. Use when decomposition plus a trend forecaster is the right strategy; `uses_exog=False`.
- **MFLES** — `season_length` as an int, list, or None, `fourier_order`, `max_rounds`, `ma`, `alpha`, `decay`, `changepoints`, `n_changepoints`, `seasonal_lr`, `trend_lr`, `exogenous_lr`, `residuals_lr`, `cov_threshold`, `moving_medians`, `min_alpha`, `max_alpha`, `trend_penalty`, `multiplicative`, `smoother`, `robust`, `verbose`, `alias='MFLES'`, `prediction_intervals`. Use for configurable multi-seasonal modeling; `uses_exog=True`.
- **TBATS** — `season_length` as an int or list, `use_boxcox=True`, `bc_lower_bound`, `bc_upper_bound`, `use_trend=True`, `use_damped_trend=False`, `use_arma_errors=False`, `alias='TBATS'`. Use for complex seasonal patterns with native interval support.

### Theta family
Use these when the theta method is the best conceptual fit or when you want a theta-based benchmark.
These models support the direct array API and simulation.

- **Theta** — `season_length`, `decomposition_type='multiplicative'`, `alias='Theta'`, `prediction_intervals`.
- **OptimizedTheta** — `season_length`, `decomposition_type='multiplicative'`, `alias='OptimizedTheta'`, `prediction_intervals`.
- **DynamicTheta** — `season_length`, `decomposition_type='multiplicative'`, `alias='DynamicTheta'`, `prediction_intervals`.
- **DynamicOptimizedTheta** — `season_length`, `decomposition_type='multiplicative'`, `alias='DynamicOptimizedTheta'`, `prediction_intervals`.

### Volatility
Use these for variance modeling and financial-style time series.
They are more fragile than simple baselines and need finite numeric input.

- **GARCH** — `p`, `q`, `alias='GARCH'`, `prediction_intervals`. Use when conditional variance matters; forecast output includes conditional variance `sigma2`.
- **ARCH** — `p`, `alias='ARCH'`, `prediction_intervals`. Use as the `q=0` special case of GARCH.

### Machine learning and fallback models
Use these when you need a learned regressor wrapper or a safe fallback output.

- **SklearnModel** — `model`, `prediction_intervals`, `alias`. Use for any scikit-learn regressor; `uses_exog=True` and `scikit-learn` is required.
- **ConstantModel** — `constant`, `alias='ConstantModel'`. Use when you want a deterministic fallback that returns the same value and degenerate intervals.
- **ZeroModel** — `alias='ZeroModel'`. Use as a constant-zero fallback.
- **NaNModel** — `alias='NaNModel'`. Use as an explicit failure sentinel or placeholder.

### Optional adjacent adapter
- **AutoARIMAProphet** — available from `statsforecast.adapters.prophet` when `prophet` is installed, or legacy `fbprophet` in older environments. It is not a core model class, but it can help replace Prophet-style workflows with an AutoARIMA backend.

### Advanced state-space model
- **UCM** — `level`, `trend`, `seasonal`, `cycle`, `autoregressive`, `irregular`, `stochastic_level`, `stochastic_trend`, `stochastic_seasonal`, `stochastic_cycle`, `damped_cycle`, `cycle_period_bounds`, `use_exact_diffuse`, `fit_method`, `maxiter`, `alias`. Use for structural time-series modeling with statsmodels-style components; `uses_exog=True`.

## Common alias patterns
- `RWD` -> `RandomWalkWithDrift`
- `SES` -> `SimpleExponentialSmoothing`
- `SESOpt` -> `SimpleExponentialSmoothingOptimized`
- `SeasESOpt` -> `SeasonalExponentialSmoothingOptimized`
- `SeasWA` -> `SeasonalWindowAverage`
- `SklearnModel` defaults to the wrapped estimator class name when `alias=None`
- `StatsForecast` treats the model name as the alias or `repr(model)`, so use a custom `alias` whenever two models would otherwise collide
