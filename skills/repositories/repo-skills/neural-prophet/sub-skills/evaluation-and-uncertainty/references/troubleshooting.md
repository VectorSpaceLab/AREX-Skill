# Evaluation and uncertainty troubleshooting

Use this guide when validation, cross-validation, quantile, conformal, or interval-evaluation workflows fail or produce confusing output.

## Quantile configuration errors

**Symptoms**

- `Quantiles must be provided as list.`
- `The quantiles specified need to be floats in-between (0, 1).`
- Forecast columns do not include the expected interval bounds.

**Recovery**

- Pass `quantiles` as a list, not a scalar or string: `NeuralProphet(quantiles=[0.05, 0.95])`.
- Every quantile must satisfy `0 < q < 1`; do not use percentages such as `5` or boundary values `0`/`1`.
- You do not need to include `0.5`; NeuralProphet inserts the median internally and avoids duplicate median columns.
- If you only pass median behavior (`quantiles=None`, `[]`, or `[0.5]`), interval percent columns are not created. Add a lower/upper pair for interval workflows.

## Asymmetrical alpha with the wrong conformal method

**Symptoms**

- `ValueError` stating that asymmetrical coverage errors are not available for the naive method.

**Recovery**

- For `method="naive"`, pass scalar `alpha`, for example `alpha=0.1` for a 90% interval.
- For asymmetrical left/right tail errors, switch to `method="cqr"` and pass a tuple such as `alpha=(0.03, 0.07)`.
- Keep the tuple values as error rates, not target coverages. A tuple should sum to the total desired error rate.

## Calibration/test split confusion

**Symptoms**

- Conformal intervals look too optimistic.
- `uncertainty_evaluate` reports unexpectedly low miscoverage.
- Evaluation data appears to overlap with training data.

**Recovery**

- Use three time-ordered sets: `train -> calibration -> test`.
- Fit only on `train_df`.
- Pass the middle holdout to `calibration_df` and the final holdout as the `df` argument to `conformal_predict`.
- Do not tune hyperparameters on the test set. If you tune on validation data, keep calibration and test separate from that validation process.
- For evaluation, pass a test dataframe with observed `y`. Future-only rows can receive intervals but cannot be scored for miscoverage.

## Leakage, lags, and fold overbleed

**Symptoms**

- Split or fold row counts seem larger than expected.
- Initial validation rows reuse dates that also appear near the end of training.
- Autoregressive or lagged-regressor CV appears to leak information.

**Recovery**

- NeuralProphet split helpers preserve target separation but may allow input overbleed so validation rows have the historical context needed by `n_lags` or lagged regressors.
- Treat rows reused only as lag inputs differently from target leakage. Report this behavior when interpreting fold sizes.
- Reduce `n_lags`, reduce `fold_overlap_pct`, or use a simpler holdout when independence is more important than keeping full lag context.
- For multi-`ID` cross-validation, prefer `global_model_cv_type="global-time"` when leakage avoidance matters. Use `local` only when per-series local fold sizes matter and cross-series date leakage is acceptable; use `intersect` when equal counts and no cross-series leakage are required, accepting that non-overlapping dates are dropped.

## Empty or missing metrics

**Symptoms**

- `fit(...)` returns `None`.
- Training progress plot is unavailable or falls back to a progress bar.
- Metric columns such as `MAE`, `RMSE`, `MAE_val`, or `RMSE_val` are absent.

**Recovery**

- Do not pass `minimal=True` when you need fit metrics; it disables metrics, progress, and checkpointing.
- Do not pass `metrics=False`. Use `metrics=True`, a supported list such as `metrics=["MAE", "RMSE"]`, or rely on constructor `collect_metrics=True`.
- `progress="plot"` requires metrics to be enabled. For non-interactive verification scripts, use `progress=None` and inspect returned metric dataframes instead.
- `test(df)` returns holdout metrics from the fitted model; use it when you disabled training metrics but still need a holdout score.

## Expensive cross-validation

**Symptoms**

- CV takes much longer than a single fit.
- Memory or runtime grows with many folds, large folds, or heavy lagged models.

**Recovery**

- Remember that each fold trains a fresh model. Start with `k=3`, small `fold_pct` such as `0.1`, and `fold_overlap_pct=0.0` for smoke checks.
- Disable plotting and checkpoints during fold loops: `fit(..., progress=None, checkpointing=False)`.
- Set explicit small `epochs`, `batch_size`, and `learning_rate` for diagnostic CV before running a final benchmark.
- Prefer one holdout split when the goal is a fast sanity check rather than a robust backtest distribution.

## Interval evaluation returns empty, NaN, or fails

**Symptoms**

- `uncertainty_evaluate` cannot infer interval columns.
- The evaluation summary contains NaN values or is empty.

**Recovery**

- Ensure the forecast dataframe came from a quantile or conformal workflow and includes percent interval columns or `qhat` interval columns.
- Ensure rows used for evaluation contain both observed `y` and a non-null `yhat1`. The evaluator drops rows missing either column.
- For multi-step forecasts, inspect interval columns for every `yhat<i>` step you plan to score.
- When using `show_all_PI=True`, compare conformal columns containing `qhat` against original quantile columns containing `%` to confirm which interval is being evaluated.

## Package/environment failures before evaluation starts

**Symptoms**

- Import or training fails before any split/evaluation code runs.
- Errors mention pandas removed APIs, `pkg_resources`, Lightning/Fabric, or optional plotting packages.

**Recovery**

- This NeuralProphet release requires a pandas version before pandas 3 because it relies on pandas APIs removed in pandas 3.
- Some Lightning/Fabric combinations used by this release expect `pkg_resources`; use a setuptools version before the removal of that compatibility layer.
- Optional interactive plotting support is not required for evaluation. Leave `plotting_backend=None` in `conformal_predict` for headless checks, and route plotting-extra/debugging work to `../operations-and-migration/SKILL.md`.
