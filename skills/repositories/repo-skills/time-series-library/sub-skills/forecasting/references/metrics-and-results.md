# Forecasting Metrics and Results

## Long-term and zero-shot metrics

Long-term and zero-shot forecast experiments collect predictions and truths, then compute:

- MAE
- MSE
- RMSE
- MAPE
- MSPE
- Optional DTW when `--use_dtw` is set

The metric array is saved as:

```text
results/<setting>/metrics.npy  # [mae, mse, rmse, mape, mspe]
results/<setting>/pred.npy
results/<setting>/true.npy
```

A human-readable summary is appended to `result_long_term_forecast.txt` or `result_zero_shot_forecast_search.txt` at the source-tree working directory.

## M4 metrics

Short-term/M4 uses loss functions such as SMAPE, MAPE, or MASE during training and writes per-season forecast CSVs:

```text
m4_results/<model>/<SeasonalPattern>_forecast.csv
```

`M4Summary.evaluate()` prints SMAPE, MAPE, MASE, and OWA only when all six seasonal forecast files exist: `Yearly`, `Quarterly`, `Monthly`, `Weekly`, `Daily`, and `Hourly`.

## Plot outputs

Forecast experiments write PDF plots under:

```text
test_results/<setting>/
```

These are sampled visualizations, not complete prediction archives. Use `pred.npy` and `true.npy` for programmatic analysis.

## Interpreting poor metrics

- First confirm the data split and scaling behavior; tiny custom smoke data is not a benchmark.
- Confirm `--features`, `--target`, and channel counts before changing model size.
- For MAPE/MSPE, zero or near-zero true values can dominate ratios.
- For DTW, `--use_dtw` can be very slow and should not be enabled by default.
- For M4, compare only after the appropriate seasonal pattern and all expected forecast files are present.
