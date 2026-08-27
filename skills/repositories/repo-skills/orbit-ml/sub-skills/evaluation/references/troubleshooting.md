# Troubleshooting

## Purpose

Use this file when a backtest, metric, plot, or WBIC/BIC check fails. Each row names the symptom, likely cause, and the next recovery step.

## Common failures

| Surface | Symptom or error fragment | Likely cause | Recovery step |
|---|---|---|---|
| Split parameters | `min_train_len and n_splits cannot both be None` | No split basis was supplied | Set either `min_train_len` or `n_splits` before creating the splitter/backtester. |
| Split parameters | `unknown window type` | `window_type` is neither `expanding` nor `rolling` | Use one of the supported window types. |
| Split parameters | `holdout period length must be positive` | `forecast_len <= 0` | Choose a positive forecast horizon. |
| Split parameters | `required time span is more than the full data frame` | Train window plus forecast horizon exceeds available rows | Reduce the horizon or the minimum training length. |
| Split parameters | Empty or degenerate folds | `n_splits`, `incremental_len`, and `forecast_len` do not fit the data | Recalculate the fold plan from the full series length before retrying. |
| Datetime handling | `date_col not found in df provided` | The supplied date column name is wrong | Rename the column or pass the correct one. |
| Datetime handling | Plot or backtest order looks scrambled | Dates are unsorted or duplicated | Sort the dataframe by date and remove/resolve duplicates before splitting or plotting. |
| Datetime handling | `Prediction df dates is not ordered` | `plot_predicted_data()` received unordered prediction dates | Sort the prediction dataframe by the date column first. |
| Empty plot inputs | `No prediction data or training response to plot.` | One of the plot inputs is empty | Check that the fit/predict step produced non-empty dataframes. |
| Empty plot inputs | `prediction_percentiles has to be None or a list with length=2.` | Wrong interval list length | Pass exactly two percentiles or leave the argument as `None`. |
| Empty plot inputs | `plot_components` yields nothing or a zero-row layout | None of the requested components exist in the dataframe | Inspect the prediction output columns and only request present components. |
| Metric signatures | `metric callable does not have a supported function signature` | Callable argument names do not match Orbit's contract | Rename the callable arguments to `actual`/`prediction` or use the accepted test/train signature names. |
| Metric signatures | `BackTester.score()` returns only test rows for a custom metric | The metric needs train/test-specific arguments and is excluded from training scoring | Only `actual`/`prediction` metrics participate in `include_training_metrics=True`. |
| NaN handling | `NaN` metric values or unstable RMSSE | Missing values, zeros, or a degenerate lag-1 denominator | Remove or impute missing values before scoring, and prefer `mae`, `mse`, `smape`, or `wmape` when RMSSE is not stable. |
| NaN handling | Unexpectedly filtered rows | The metric drops rows with zero or near-zero actuals | Check whether the series has many zeros; consider a different metric. |
| Matplotlib backend | `TclError: no display name and no $DISPLAY environment variable` | Interactive backend in a headless session | Set a non-interactive backend such as `Agg`, or call plotting helpers with `is_visible=False`. |
| Matplotlib backend | Figure saves but nothing is shown | `is_visible=False` or no display backend | This is expected in smoke runs; check the saved file or switch to a visible backend locally. |
| Residual diagnostics | `ModuleNotFoundError: No module named 'statsmodels'` | `orbit.diagnostics.plot` imports statsmodels at module import time, so every plot helper needs it | Install the package requirement for the diagnostics plot path, then rerun any plot import or plot call. |
| GIF export | No GIF appears after `export_gif=True` | `imageio` is missing or `fig_dir` does not exist | Create the directory first and install `imageio` before retrying. |
| WBIC vs BIC | `orbit.diagnostics.metrics.wbic()` does nothing useful | Wrong entry point | Use `model.fit_wbic()` / `model.get_wbic()` for WBIC and `model.fit(); model.get_bic()` for BIC. |
| WBIC flow | `Sampling temperature is not log(n); WBIC calculation is not valid!` | `get_wbic()` was called on a model not fit with WBIC temperature | Refit through `fit_wbic(df)` and then call `get_wbic()` again. |
| BIC flow | BIC unavailable on a non-MAP fit | The model was not fit with the MAP path | Fit the model with its MAP estimator before calling `get_bic()`. |

## Recovery checklist

1. Verify the dataframe is sorted by the date column and has the expected columns.
2. Confirm the split configuration leaves enough history and holdout data.
3. Check metric callable argument names against the supported contract.
4. For plotting, use a headless backend or `is_visible=False`.
5. For residual plots, confirm `statsmodels` is installed.
6. For WBIC/BIC, call the model-level method that matches the estimator family.
