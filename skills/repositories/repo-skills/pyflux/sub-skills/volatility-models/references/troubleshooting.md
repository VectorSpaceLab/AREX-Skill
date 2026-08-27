# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import or network failures in copied examples | The original docs/tests rely on live Yahoo or FRED data readers | Replace them with a local synthetic return series or a local CSV fixture; the model code is not the problem. |
| Volatility estimates look flat, unstable, or nonsensical | The series is in price levels instead of returns/log returns | Convert prices to returns first, then refit. |
| `add_leverage()` seems to do nothing | It was never called, or it was called after fitting | Call `add_leverage()` before `fit()` and refit the model. |
| `SEGARCH` or `SEGARCHM` warns that skew t is not well-suited for MLE/MAP | The skew-t path is fragile and slower than the t-based families | Use `BBVI` or `M-H`; if skewness is not essential, switch to `EGARCH` or `EGARCHM`. |
| `EGARCHMReg.predict()` throws a shape or unpacking error | The OOS regression path is fragile, or `oos_data` does not match the formula columns | Use the runtime constructor order `EGARCHMReg(data, p, q, formula)`, provide a DataFrame with all formula columns, and validate with `predict_is()` first. |
| `sample()` or `ppc()` says no latent variables were estimated | Those methods only work after a Bayesian fit | Refit with `BBVI` or `M-H`. |
| Prediction intervals look too narrow | MLE/BBVI intervals do not fully propagate latent-variable uncertainty | Use `M-H` when you need the strongest Bayesian interval story. |
| `EGARCHMReg` fit or forecast behavior seems inconsistent with the docs | The docs page prints a different constructor order than the runtime signature | Use `EGARCHMReg(data, p, q, formula)` and keep the formula in a pandas DataFrame. |

## Quick checks

- `fit()` should return a results object and update `latent_variables`.
- `predict(h=n)` and `predict_is(h=n)` should return `n` rows.
- `plot_sample()` and `plot_ppc()` require `BBVI` or `M-H`.
- If a forecast path fails, reduce to a smaller synthetic series and run the bundled smoke helper section again.
