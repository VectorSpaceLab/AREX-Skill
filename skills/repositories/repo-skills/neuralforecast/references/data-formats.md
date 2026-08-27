# Data Formats

## Purpose

Read this when the task is about panel layout, required columns, exogenous
variables, categorical features, local scaling, or converting a pandas/Polars
frame into the NeuralForecast dataset objects.

## Core panel contract

NeuralForecast expects long-format panel data with at least these columns:

| Column | Meaning | Typical type |
| --- | --- | --- |
| `unique_id` | series identifier | string, category, or integer-like |
| `ds` | timestamp or integer step | pandas datetime / integer index |
| `y` | target value | numeric |

Optional but common columns:

| Column family | Meaning | Notes |
| --- | --- | --- |
| historical exogenous | values available only up to the forecast origin | include in `hist_exog_list` |
| future exogenous | values known for the forecast horizon | include in `futr_exog_list` and provide `futr_df` for prediction |
| static exogenous | series-level features | place in `static_df` keyed by `unique_id` |
| categorical exogenous | columns to embed instead of scale | declare in `cat_exog_list` and provide `categorical_cardinalities` |
| `available_mask` | per-row mask for missing/withheld observations | must be binary/boolean-like |
| `sample_weight` | per-row weighting | must be non-negative |

## Dataset helpers

- `TimeSeriesDataset.from_df(df, static_df=None, id_col='unique_id', time_col='ds', target_col='y')`
  converts a long-format frame into tensor-backed panel storage.
- `TimeSeriesDataModule(dataset, batch_size=32, valid_batch_size=1024, drop_last=False, shuffle_train=True, **dataloaders_kwargs)`
  batches a prepared dataset for model training and inference.
- `generate_series(...)` is the safest local fixture generator for tests and
  smoke checks.

## Validation order to remember

1. Check that the panel has `unique_id`, `ds`, and `y`.
2. Check that rows are sorted or can be sorted by `unique_id` and `ds`.
3. Check that `ds` is monotonic inside each series.
4. Check that required exogenous columns exist in the right frame.
5. Check that `futr_df` covers the required horizon without nulls.
6. Check that categorical columns have declared cardinalities.
7. Check that `sample_weight` is non-negative and that `available_mask` is usable.

## Common errors and what they mean

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| Missing `unique_id`, `ds`, or `y` | Wrong dataframe shape | Run `scripts/validate_panel.py`. |
| `Found missing values in [...]` | Nulls in target, static, or exogenous columns | Fill or drop the offending rows. |
| `There are missing combinations` | `futr_df` does not cover every required series/date pair | Build the full future frame for all series and horizons. |
| `Dropped ... unused rows` warning | `futr_df` has extra rows | Trim the future frame to the expected combinations. |
| Categorical cardinality error | Declared cardinalities are too small | Increase the declared cardinality or reduce categories. |
| Sample weight error | Negative or null weights | Clean the `sample_weight` column. |

## Local scaling reminders

- `local_scaler_type` applies to temporal inputs.
- `local_static_scaler_type` applies to static exogenous columns.
- Supported values observed in source and tests: `standard`, `robust`,
  `robust-iqr`, `minmax`, and `boxcox`.
- Scaling is inverted after prediction when the model uses local scalers.

## Polars notes

- The panel helpers accept both pandas and Polars dataframes in the main paths.
- If a workflow fails only on Polars, check column names, dtypes, and category
  handling first.

## Read next

- `workflows.md` for a quick end-to-end panel example.
- `troubleshooting.md` for data-structure failure recovery.
