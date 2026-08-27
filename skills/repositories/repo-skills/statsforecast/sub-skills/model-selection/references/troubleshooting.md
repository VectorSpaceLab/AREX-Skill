# Troubleshooting

This page covers model-selection problems, not panel orchestration or distributed backend routing.
If the issue is about `StatsForecast`, `X_df`, `n_jobs`, or grouped DataFrame workflows, route back to core-forecasting.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MFLES requires scikit-learn` or a constructor-time import error from `AutoMFLES` | `scikit-learn` is missing | Install `scikit-learn` before using `AutoMFLES`; the constructor checks for it immediately. |
| `ImportError` / `ModuleNotFoundError` when wrapping a regressor with `SklearnModel` | `scikit-learn` is missing or broken | Install `scikit-learn`; `SklearnModel` imports `sklearn.base.clone` during fit/forecast calls. |
| `Model names must be unique` | Two models resolved to the same name or alias | Set distinct `alias` values before passing the models to `StatsForecast`. |
| Exogenous features appear to be ignored | The chosen class does not actually consume exogenous inputs | Use an exogenous-aware model (`AutoARIMA`, `ARIMA`, `AutoRegressive`, `AutoMFLES`, `SklearnModel`, or `UCM`) or move the question to core-forecasting/feature-engineering. |
| `X_future` shape mismatch or forecast length mismatch | The future regressor matrix does not match the horizon | Pass one future row per forecast step and keep the column order identical to training `X`. |
| `prediction intervals` error about too few samples | The series is too short for the requested horizon/window setup | Reduce `h`, reduce the number of conformal windows, or collect more history. |
| Seasonal model looks wrong or overfits | `season_length` does not match the real sampling frequency | Use the real period for the data; for multiple seasonalities, pass a list to `MSTL` or `TBATS`. |
| `AutoMFLES` performs poorly or fails to search well | `test_size`, `step_size`, or `season_length` are mis-specified | Make sure the test window is meaningful for the series length; `step_size` defaults to `test_size` if omitted. |
| `WindowAverage` / `SeasonalWindowAverage` returns `NaN` | The history is shorter than the configured window | Lower `window_size` or pick a simpler baseline. |
| Intermittent demand forecasts look unstable | A generic smoother or ARIMA-style model was chosen for a sparse series | Switch to `ADIDA`, a Croston variant, `IMAPA`, or `TSB`; use `ZeroModel` or `ConstantModel` only when a fallback is appropriate. |
| `GARCH` / `ARCH` fitting fails or produces invalid-looking variance output | The input contains NaN/Inf values, negative variance behavior, or badly scaled data | Clean the series, keep it finite, and consider a simpler fallback model if volatility fitting remains unstable. |
| Optional Prophet adapter import fails | `prophet` / `fbprophet` is not installed | Install the optional dependency only if you need `AutoARIMAProphet`; it is separate from the core model catalog. |
