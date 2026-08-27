# Troubleshooting

Use this when Chronos data validation fails before forecasting.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing `item_id`, `timestamp`, or target columns | The context DataFrame is not in Chronos long format | Add the required columns and pass the target names through `target` / `target_columns`. |
| Timestamp parse failure | `timestamp` values are not datetime-like or contain invalid strings | Parse with `pd.to_datetime(...)` before validation and clean invalid rows. |
| Irregular timestamps in one series | Gaps, repeats, or mixed spacing inside a series | Rebuild the series with a regular frequency or normalize the source calendar first. |
| Inconsistent frequencies across series | Different items use different cadences | Resample or split the data so every series has one shared frequency. |
| Frequency cannot be inferred | Every series is too short to pin down a cadence, or the data are irregular | Supply an explicit `freq` to the validator / caller, or keep at least one regular series with 3+ points. |
| `future_df` has the wrong IDs | The future frame is missing series or includes extras | Regenerate the future frame from the context series list. |
| `future_df` has the wrong number of rows | Not exactly `prediction_length` rows per item | Use `make_future_df(...)` or rebuild each future block to match the horizon exactly. |
| `future_df` timestamp mismatch | Future timestamps do not continue from the context frequency | Regenerate the future frame from the validated context timestamps and cadence. |
| `future_df` contains target columns | Forecast targets were copied into the future frame | Remove all target columns from `future_df`. |
| `future_df` contains unrelated extra columns | The future frame has columns absent from the context | Drop the extra columns or add them to the context if they are meant to be covariates. |
| Covariate key mismatch in list-of-dicts | `past_covariates` keys differ across items or future keys are not a subset of past keys | Make every series use the same covariate keys and keep future keys within the past-covariate set. |
| Covariate length mismatch in list-of-dicts | A covariate array does not match the history length or prediction length | Rebuild the arrays so past covariates match history length and future covariates match the horizon. |
| Categorical covariates look encoded differently than expected | Bool/object/string columns are treated as categorical | Accept the encoding path, or convert the column to the intended numeric representation before preprocessing. |
| Unseen future category behaves oddly | Target encoding maps unseen strings to the item mean; ordinal encoding can yield NaN | Keep the categorical vocabulary consistent, or choose the encoding mode intentionally. |
| Forecast looks like target leakage | A future feature accidentally contains target information | Remove any post-horizon target-derived feature from `future_df`. |
| Validation passes only when `validate_inputs=False` | The data depend on Chronos' normalization or inference safety net | Treat that as a repair signal: sort by series/timestamp, align IDs, and rebuild the future horizon before disabling validation. |

## Practical repair order

1. Fix column names and dtypes.
2. Convert timestamps to datetime.
3. Check each series for regular cadence and duplicate timestamps.
4. Rebuild `future_df` with `make_future_df`.
5. Re-run the validator script.

## Notes on `validate_inputs=False`

- `predict_df(..., validate_inputs=False)` skips the safety checks that catch
  misaligned timestamps and series mismatches.
- `from_data_frame(..., validate_inputs=False)` expects already-prepared data;
  Chronos will not repair malformed rows for you.
- When in doubt, validate first, then only disable validation after the data are
  proven to be canonical.
