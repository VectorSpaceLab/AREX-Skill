# Evaluation and uncertainty API reference

This reference lists the NeuralProphet APIs needed for validation, testing, cross-validation, quantile regression, split conformal prediction, and interval evaluation.

## Evaluation APIs

| API | Purpose | Inputs and parameters | Returns / output |
| --- | --- | --- | --- |
| `NeuralProphet(..., quantiles=None, collect_metrics=True, n_forecasts=1, n_lags=0, learning_rate=None, epochs=None, batch_size=None, normalize="auto", accelerator=None, trainer_config=None)` | Construct a model with optional quantile regression and metric collection. | `quantiles` must be a list of floats strictly between 0 and 1 or `None`; `collect_metrics=True` enables default `MAE` and `RMSE` collection. | A configured, unfitted forecaster. Internally the median `0.5` quantile is always present and is not duplicated. |
| `fit(df, freq="auto", validation_df=None, epochs=None, batch_size=None, learning_rate=None, early_stopping=False, minimal=False, metrics=None, progress="bar", checkpointing=False, deterministic=False, trainer_config=None)` | Train the model and optionally evaluate each epoch on `validation_df`. | `df` is the training dataframe; `validation_df` is a held-out later dataframe; `metrics` overrides constructor metric collection; `minimal=True` disables metrics, progress, and checkpointing. | Metrics dataframe when metrics are enabled; otherwise `None`. Validation metric columns use validation suffixes such as `_val`. |
| `test(df, verbose=True)` | Evaluate a fitted model on a holdout dataframe. | `df` must contain observed `y` and all columns required by the fitted model. | Metrics dataframe from the fitted trainer/model. |
| `split_df(df, freq="auto", valid_p=0.2, local_split=False)` | Create a time-ordered train/validation or train/test split. | `valid_p` is a fraction in `(0, 1)` or an integer count of validation samples; `local_split=True` splits each `ID` locally. | `(df_train, df_val)` with earlier rows in `df_train` and later rows in `df_val`. |
| `crossvalidation_split_df(df, freq="auto", k=5, fold_pct=0.1, fold_overlap_pct=0.5, global_model_cv_type="global-time")` | Create rolling-origin cross-validation folds. | `k` folds; `fold_pct` validation size; `fold_overlap_pct` validation overlap; multi-series modes are `global-time`, `local`, and `intersect`. | List of `k` `(df_train, df_val)` tuples. |
| `double_crossvalidation_split_df(df, freq="auto", k=5, valid_pct=0.1, test_pct=0.1)` | Create separate rolling validation and test fold sets for one time series. | Use only with a single time series; multi-`ID` data is not supported by this helper. | `(folds_val, folds_test)`, each shaped like the output of `crossvalidation_split_df`. |

## Uncertainty APIs

| API | Purpose | Inputs and parameters | Returns / output |
| --- | --- | --- | --- |
| `conformal_predict(df, calibration_df, alpha, method="naive", plotting_backend=None, show_all_PI=False, **kwargs)` | Add split conformal prediction intervals to forecasts. | `df` is the test or prediction dataframe; `calibration_df` is a held-out calibration dataframe; `alpha` is a scalar error rate for symmetrical intervals or a tuple for asymmetrical CQR; `method` is `"naive"` or `"cqr"`; `kwargs` are forwarded to `predict`, for example `decompose=False`. | Forecast dataframe with interval columns. With `show_all_PI=True`, both conformal interval columns and quantile-regression interval columns are retained. |
| `uncertainty_evaluate(df_forecast)` | Score interval forecasts on observed rows. | `df_forecast` must include `y`, `yhat1`, and interval columns from quantile or conformal prediction. | Dataframe with MultiIndex columns for each forecast step, including `interval_width` and `miscoverage_rate`. |

## Quantile and interval column semantics

| Column pattern | Meaning |
| --- | --- |
| `yhat1`, `yhat2`, ... | Median point forecasts. `yhat<i>` is the i-step-ahead forecast aligned to the target timestamp. |
| `yhat1 5.0%`, `yhat1 95.0%` | Quantile-regression lower/upper interval columns for requested non-median quantiles. Percent values reflect the quantiles passed to `NeuralProphet`. |
| `yhat1 - qhat1`, `yhat1 + qhat1` | Naive conformal interval columns when `show_all_PI=True`. They are symmetric around `yhat1`. |
| `yhat1 95.0% - qhat1`, `yhat1 5.0% + qhat1` | CQR conformalized interval columns when `show_all_PI=True`. They adjust the quantile-regression interval. |
| `("yhat1", "interval_width")` | Mean upper-minus-lower interval width returned by `uncertainty_evaluate`. |
| `("yhat1", "miscoverage_rate")` | Fraction of observed targets outside the interval returned by `uncertainty_evaluate`; lower is better for a fixed target coverage. |

## Behavioral notes

- `quantiles=None`, `quantiles=[]`, and no `quantiles` argument all produce median-only behavior. Any user-supplied `0.5` is kept as the single median entry rather than duplicated as a percent column.
- Invalid quantile configuration raises early: `quantiles` must be a list, and every value must be strictly between 0 and 1.
- `method="naive"` accepts only scalar `alpha`. For asymmetrical tail errors such as `(0.03, 0.07)`, use `method="cqr"`.
- `uncertainty_evaluate` drops rows with missing `y` or `yhat1`. Future-only rows without ground truth can carry intervals but cannot be scored for miscoverage.
- Validation and test metrics can be affected by normalization choices. With local normalization, metrics may be reported in normalized scale.
- Autoregressive models and lagged regressors need historical context rows around split boundaries. Row counts in splits and folds therefore include lag input rows, not just independent target rows.
- Core `predict` and `make_future_dataframe` mechanics are covered by the sibling core-forecasting sub-skill; this reference only documents the evaluation-specific use of `conformal_predict` and `test`.
