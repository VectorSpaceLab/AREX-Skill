# Model-selection troubleshooting

Use these bounded diagnoses for pmdarima v2.1.1 at commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`. Fix data and geometry contracts
before relaxing estimator settings.

## Split and fold geometry

| Symptom | Cause | Recovery |
|---|---|---|
| `h must be a positive value` | `h < 1` at splitter construction | Choose a positive forecast horizon. |
| `step must be a positive value` | `step < 1` | Choose a positive origin advance. |
| `Initial training size must be a positive integer` | Explicit rolling `initial < 1` | Increase `initial`; it is a count. |
| Initial training size plus horizon exceeds the series | No complete first rolling fold | Reduce `initial`/`h` or collect more observations. |
| Window size plus horizon exceeds the series | No complete first sliding fold | Reduce `window_size`/`h` or collect more observations. |
| `window_size must be > 2` | Sliding window has fewer than 3 rows | Use at least 3, and generally more for ARIMA. |
| Default splitter returns no folds | Short input plus default `max(1,n//3)` or `max(3,n//5)` leaves no complete horizon | Materialize folds, choose explicit feasible bounds, and reject empty CV. |
| `check_cv` rejects the splitter | String, random K-fold, or unrelated validator | Use `None`, `RollingForecastCV`, or `SlidingWindowForecastCV`. |
| Folds are geometrically valid but fitting fails | History is insufficient for differencing, seasonal terms, or estimator initialization | Increase training history, reduce model capacity, or route model choice to [forecasting](../../forecasting/SKILL.md); do not leak future rows. |

For explicit valid geometry, plan no more than
`1 + floor((n - initial - h)/step)` rolling or
`1 + floor((n - window_size - h)/step)` sliding folds, then verify the actual
list. Every test block must be complete and after its training block.

## Holdout and exogenous alignment

| Symptom | Cause | Recovery |
|---|---|---|
| Inconsistent numbers of samples | `len(y) != X.shape[0]` | Validate row counts before `train_test_split` or CV and pass paired inputs in one call. |
| Fit succeeds but prediction fails on one fold | `X_test` has wrong row count/width/order or missing values | Inspect `X_train` and `X_test`; preserve a fixed schema and exactly `h` future rows. |
| Label-indexed data shifts | API indexes positionally, not by timestamp joins | Sort once, record the order, and verify integer indices. |
| Fold split accepts `X` but evaluator fails later | Split geometry is based on `y`; slicing both occurs during fitting | Validate `X` before fitting and check every test block. |
| Forecast uses realized future target | Target-derived feature or imputation leaked across the boundary | Recompute causally inside each fold, use a valid future feature forecast, or remove the feature. |
| Feature transform was fit on all rows | Preprocessing learned from test/future rows | Put the full transform and estimator in a cloneable pipeline; route implementation to [preprocessing](../../preprocessing/SKILL.md). |

The package does not invent future exogenous values. A future `X` table must be
known at the forecast origin, have the training column order, and have one row
per predicted period.

## Scoring and fit errors

| Symptom | Cause | Recovery |
|---|---|---|
| `scoring=None` or callable/type error | Scoring is required and must be a string/callable | Use `smape`, `mean_absolute_error`, `mean_squared_error`, or `metric(y_true,y_pred)`. |
| Scorer name rejected | Names are exact | Use one of the three supported names. |
| Custom scorer receives wrong order | Callable contract misunderstood | Define `(y_true, y_pred)`; true test values come first. |
| Scores selected backwards | Raw pmdarima errors were treated as utility scores | Lower MAE, MSE, and SMAPE is better. Document custom direction. |
| SMAPE is `NaN` | A zero/zero pair creates a zero denominator, or predictions are non-finite | Inspect the pair/prediction; define a zero policy or choose MAE/MSE without hiding non-finite values. |
| `ModelFitWarning` plus numeric/NaN fold result | Numeric `error_score` replaced an estimator fit error | Use `error_score="raise"` for strict selection, or retain warning, fold, exception, and sentinel in the report. |
| `error_score=None` rejected | Only `'raise'` or numeric values are valid | Select `'raise'` or a numeric sentinel deliberately. |
| Scoring error still raises | Fit fallback does not handle post-fit prediction/scorer errors | Fix predictor output/scorer shape and test one fold manually. |

## Prediction placement

| Symptom | Cause | Recovery |
|---|---|---|
| `CV step cannot be > CV horizon` | `cross_val_predict` would create gaps | Use `step <= h`, or use scalar `cross_val_score` if sparse folds are intentional. |
| Averaged output is shorter than `y` | Training and uncovered positions are omitted by design | Zip output to the union of materialized test positions. |
| Overlap changes predictions | Multiple folds forecast the same target position | Choose mean versus median explicitly and retain folds/raw forecasts. |
| Raw output contains `NaN` | Training/uncovered positions have no forecast | Expected for sparse `(n_samples, h)` output; never fill from true targets. |
| Output has no timestamp/index | API returns NumPy arrays | Reattach labels only after positional mapping. |
| `cross_val_predict` fails unexpectedly | Empty folds, fit error, or fold-specific `X` issue | Materialize folds, run one fold manually with `fit(y[train], X=X[train])` and `predict(n_periods=len(test), X=X[test])`. |

The raw matrix is a horizon-oriented sparse representation. For a custom metric
or overlapping windows, retain each prediction block and its test index rather
than assuming all non-NaN cells share one simple fold layout.

## Runtime, import, and computational bounds

| Symptom | Cause | Recovery |
|---|---|---|
| CV takes too long | Too many folds, large `h`, expensive search, or unconstrained optimizer | Bound folds, `h`, order search, and estimator `maxiter`; keep one final holdout and use a fixed candidate during smoke checks. |
| Native/source example requests plotting or network data | Example is demonstration-oriented, not a safe smoke test | Use the bundled plotting-free in-memory script. |
| Script works only from checkout root | CWD-dependent invocation | Invoke the bundled script by its path; it uses only imports and in-memory data. |
| Import fails in a clean runtime | Broken compiled install or version mismatch | Check `python -c "import pmdarima"`, package dependencies, and the installed version; repair the environment outside this skill. |
| Warnings obscure fold outcome | Verbose output or convergence warnings | Use `verbose=0` normally, capture warnings, and report failed fits rather than suppressing them. |

The bundled script always uses tiny deterministic data, bounded ARIMA
configuration, `error_score="raise"`, no network/plots/credentials, and an
argument parser with `--help`.
