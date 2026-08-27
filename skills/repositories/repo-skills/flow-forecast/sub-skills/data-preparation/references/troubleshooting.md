# Data Preparation Troubleshooting

## Timezone Errors

### `ValueError: cannot supply both a tz and a timezone-naive dtype`

- **Likely cause:** a datetime column is timezone-aware and the loader tries to cast it to `datetime64[ns]` directly.
- **Fix:** normalize the column with `to_tz_naive_datetime()` before sorting or slicing.

## Missing Column Errors

### The loader fails because a required column is absent

- **Likely cause:** `target_col`, `relevant_cols`, `sort_column`, or a temporal feature name does not exist in the dataframe.
- **Fix:** compare the CSV header to the loader config and update the config first, not the loader.

## Sequence-Length Problems

### The dataset is empty or shorter than expected

- **Likely cause:** `forecast_history + forecast_length` is larger than the available rows after filtering.
- **Fix:** shorten the windows, extend the dataset, or reduce the number of dropped rows.

### A grouped or multi-series file has uneven coverage

- **Likely cause:** one or more series IDs are much shorter than the rest.
- **Fix:** validate the series lengths before using `CSVSeriesIDLoader` or `SeriesIDTestLoader`.

## NaN And Interpolation Problems

### The loader still reports NaNs after interpolation

- **Likely cause:** the interpolation helper was not configured for the correct columns or the dataframe contains structural gaps.
- **Fix:** rerun the preprocessing step, inspect the selected columns, and verify the interpolation method name.

## Series-ID Problems

### A series group cannot be found or one series is returned with the wrong length

- **Likely cause:** the series marker column or series ID column does not match the grouped values in the CSV.
- **Fix:** inspect the unique values in the grouping column and make sure they are stable across the training, validation, and test files.

## GCS And Path Problems

### `gs://` files do not load or the path is treated like a plain string

- **Likely cause:** the path is not in `gs://bucket/object` form, or the environment lacks the expected storage access.
- **Fix:** validate the URI form first, then make the credentialed path available in the environment.

## Classification Problems

### One-hot labels look wrong or an index is out of range

- **Likely cause:** the first column is not a zero-based class label, or `n_classes` is too small.
- **Fix:** encode labels as zero-based integers in the first column and increase `n_classes` if needed.

## DA-RNN Preprocessing Problems

### `TrainData` object has no attribute `feats` or `targs`

- **Likely cause:** `preprocess_da_rnn.make_data()` returned a local `TrainData(features, targets)`, but `da_rnn.train_da` expects `da_rnn.custom_types.TrainData(feats, targs)`.
- **Fix:** wrap the object with `DaTrainData(raw.features, raw.targets)` before calling `da_rnn()` or `train()`.

## Autoencoder Problems

### The reconstruction window shape is not what the model expects

- **Likely cause:** `AEDataloader` still inherits history-window logic from the base CSV loader.
- **Fix:** keep `forecast_history` aligned with the sequence you want to reconstruct and confirm `forecast_length=1`.

## When To Escalate

Stop and ask for more information when the issue depends on private data access, remote storage credentials, or a schema that is not visible in the local CSV header.
