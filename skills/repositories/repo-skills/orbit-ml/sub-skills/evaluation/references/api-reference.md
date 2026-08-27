# API reference

## Purpose

This file condenses the Orbit evaluation surface into the exact calls and output shapes that are useful during backtesting, plotting, and WBIC/BIC checks.

## Verified core signatures

These signatures were distilled from the diagnostics source and the exercised notebook/test examples.

### Splitters and backtests

- `TimeSeriesSplitter(df, forecast_len=1, incremental_len=None, n_splits=None, min_train_len=None, window_type="expanding", date_col=None)`
- `TimeSeriesSplitter.split()` → yields `(train_df, test_df, scheme, split_key)`
- `TimeSeriesSplitter.get_scheme()` → deep-copied split metadata
- `TimeSeriesSplitter.plot(fig_width=20, show_index=False, strftime_fmt="%Y-%m-%d")`
- `BackTester(model, df, **splitter_kwargs)` — `date_col` and `response_col` are read from the model, so do not pass a separate `date_col` kwarg to the backtester.
- `BackTester.fit_predict()`
- `BackTester.score(metrics=None, include_training_metrics=False)`
- `BackTester.get_predicted_df()`
- `BackTester.get_fitted_models()`
- `BackTester.get_scheme()`
- `BackTester.get_splitter()`
- `BackTester.plot_scheme(**kwargs)`

### Built-in metrics

- `smape(actual, prediction)`
- `mape(actual, prediction)`
- `wmape(actual, prediction)`
- `wsmape(actual, prediction)`
- `mae(actual, prediction)`
- `mse(actual, prediction)`
- `rmsse(test_actual, test_prediction, train_actual)`
- `wbic()` is present in `orbit.diagnostics.metrics`, but it is a stub and not a usable implementation.

### Plot helpers

- `plot_predicted_data(training_actual_df, predicted_df, date_col, actual_col, pred_col="prediction", prediction_percentiles=None, title="", test_actual_df=None, is_visible=True, figsize=None, path=None, fontsize=None, line_plot=False, markersize=50, lw=2, linestyle="-")`
- `plot_predicted_components(predicted_df, date_col, prediction_percentiles=None, plot_components=None, title="", figsize=None, path=None, fontsize=None, is_visible=True)`
- `plot_bt_predictions(bt_pred_df, metrics=smape, split_key_list=None, ncol=2, figsize=None, include_vline=True, title="", fontsize=20, path=None, is_visible=True)`
- `plot_bt_predictions2(bt_pred_df, metrics=smape, split_key_list=None, figsize=None, include_vline=True, title="", fontsize=20, markersize=50, lw=2, fig_dir=None, is_visible=True, fix_xylim=True, export_gif=False)`
- `metric_horizon_barplot(df, model_col="model", pred_horizon_col="pred_horizon", metric_col="smape", bar_width=0.1, path=None, figsize=None, fontsize=None, is_visible=False)`
- `params_comparison_boxplot(data, var_names, model_names, color_list=..., title="Params Comparison", fig_size=(10, 6), box_width=0.1, box_distance=0.2, showfliers=False)`
- `residual_diagnostic_plot(df, dist="norm", date_col="week", residual_col="residual", fitted_col="prediction", sparams=None)`

### Exploratory plots that overlap evaluation

- `ts_heatmap(df, date_col, value_col, seasonal_interval, fig_width=8, fig_height=8, normalization=False, path=None, palette=...)`
- `correlation_heatmap(df, var_list, fig_width=8, fig_height=8, path=None, fmt=".1g", palette=...)`
- `dual_axis_ts_plot(df, var1, var2, date_col, fig_width=25, fig_height=6, path=None, color1=..., color2=...)`
- `wrap_plot_ts(df, date_col, var_list, col_wrap=3, height=4, aspect=2, palettes=...)`

## BackTester metric contract

`BackTester.score()` accepts either:

1. Metrics with exactly `actual` and `prediction` arguments, or
2. Metrics whose arguments are a subset of `test_actual`, `test_prediction`, `train_actual`, and `train_prediction`.

If a callable uses a different name such as `predicted`, `y_true`, or `y_pred`, it is rejected.

## Backtest output columns

`BackTester.get_predicted_df()` returns a dataframe with at least:

- `date`
- `split_key`
- `training_data`
- `actual`
- `prediction`

If the model emits prediction intervals or component columns, those are carried through too.

`BackTester.score()` returns a dataframe with:

- `metric_name`
- `metric_values`
- `is_training_metric`

## WBIC/BIC model-level flow

- `model.fit_wbic(df)` fits with WBIC temperature logic and returns the WBIC value.
- `model.get_wbic()` reads the WBIC value from a fitted full-Bayes or SVI model.
- `model.fit(df); model.get_bic()` is the MAP/BIC path.

The runtime notebooks and tests demonstrate these methods on DLT, LGT, KTR, KTRLite, and ETS variants depending on estimator support.
