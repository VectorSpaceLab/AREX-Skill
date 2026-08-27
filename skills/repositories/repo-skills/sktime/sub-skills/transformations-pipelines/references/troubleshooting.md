# Transformations and Pipelines Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Transformer rejects `X` | Unsupported mtype or scitype | Validate with `data-interfaces`; inspect `X_inner_mtype` and scitype tags. |
| Output has unexpected rows | Series-to-features, lagging, differencing, or windows changed shape | Confirm output scitype and index behavior before chaining. |
| Leading NaNs | Lags/windows require unavailable past observations | Choose `na_handling`, truncate, or add an `Imputer`. |
| Inverse transform fails | Transformer lacks inverse support | Inspect `capability:inverse_transform` and avoid target transforms without inverse if original-scale forecasts are needed. |
| Grid search cannot find parameter | Auto-generated step names differ | Use explicit `(name, estimator)` steps and `name__param` syntax. |
| `ForecastingPipeline` did not transform target | It transforms exogenous `X` | Use `TransformedTargetForecaster` for `y`. |
| Missing `tsfresh`, `catch22`, `holidays`, torch, or TensorFlow | Optional dependency absent | Install/verify the narrow extra or use a core transformer fallback. |
