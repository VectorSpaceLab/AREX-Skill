# Forecasting Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `fh` is required or ambiguous | The forecaster needs horizon in `fit` or `predict` | Pass `fh` exactly once where the estimator expects it; inspect `requires-fh-in-fit`. |
| Predictions have wrong index | Relative/absolute horizon mismatch | Use `ForecastingHorizon(y_test.index, is_relative=False)` for holdout indexes. |
| Future `X` error | Exogenous rows do not cover forecast horizon | Align future `X` index with the horizon and verify the forecaster uses `X`. |
| Very optimistic score | Leakage from random split or transformed future information | Use temporal splitters and fit transforms only inside the training window. |
| Missing AutoARIMA/Prophet/statsforecast | Optional dependency not installed | Install the narrow forecasting extra or choose a core forecaster fallback. |
| Prediction intervals unavailable | Forecaster lacks probabilistic tag | Select a probabilistic forecaster or a wrapper that advertises interval support. |

Run `scripts/forecasting_smoke.py --json` to verify the base forecasting path.
