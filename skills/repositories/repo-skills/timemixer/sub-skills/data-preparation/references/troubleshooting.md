# TimeMixer data-preparation troubleshooting

## Missing file or wrong root path
**Symptom**: `FileNotFoundError`, `No files found using ...`, or `Could not open ...`.

**Likely cause**: The dataset root does not contain the benchmark files directly, or the file name does not match the loader convention.

**Fix**:
- Check that the root path points to the directory that actually holds the files.
- Match the exact file names used by the loader.
- For `.ts` classification data, keep the files at the top level of the root directory.

## Custom CSV missing `date` or target
**Symptom**: `KeyError: 'date'`, `KeyError` for the target column, or an error while building time marks.

**Likely cause**: The CSV does not contain the required `date` column, the target name is wrong, or the target column is not numeric.

**Fix**:
- Add a `date` column for custom and ETT-style forecasting data.
- Make sure the target column name matches the loader argument.
- Ensure all non-date columns are numeric or cleanly parseable.

## Insufficient rows for windows
**Symptom**: The dataset length becomes zero or negative, or training crashes before the first batch.

**Likely cause**: `seq_len + pred_len` is longer than the available split rows, or `win_size` is longer than the split for anomaly data.

**Fix**:
- Reduce `seq_len`, `pred_len`, or `win_size`.
- Add more rows to the source data.
- Recheck split sizes after the 70/20/10, 60/20/20, or fixed ETT partitioning.

## Pandas frequency or time-feature errors
**Symptom**: `Unsupported frequency ...` or a pandas offset parse failure.

**Likely cause**: `freq` is not a supported offset string.

**Fix**:
- Use a pandas-parsable frequency such as `h`, `t`, `15min`, `3h`, `d`, `w`, or `ms`.
- For ETT minute data, keep the minute-scale convention.
- Remember that `time_features_from_frequency_str` only supports the families documented in `references/data-formats.md`.

## sktime / UEA loader errors
**Symptom**: `ModuleNotFoundError: sktime`, `.ts` parse failures, or empty UEA datasets.

**Likely cause**: The UEA archive is not installed, the `.ts` file is malformed, or the train/test file name does not match the loader filter.

**Fix**:
- Install the `sktime` dependency used by the loader if it is missing; on Python 3.8, use the repo's `sktime==0.29.1` pin.
- Keep UEA files as valid `.ts` archives.
- Name the split files with the expected `TRAIN` / `TEST` tokens.
- If the root directory has only one split file, the loader may not find both classification splits.

## PEMS file or channel mismatch
**Symptom**: `KeyError: 'data'`, index errors on `[:,:,0]`, or a shape mismatch with `enc_in` / `c_out`.

**Likely cause**: The `.npz` archive does not expose a `data` key, or its array shape is not `[time, nodes, channels]` with at least one channel.

**Fix**:
- Ensure the archive has a `data` key.
- Ensure the array is three-dimensional.
- Set the model input and output channel counts to the node count in the second dimension after slicing.

## Solar parse or row issues
**Symptom**: `ValueError` while converting rows to float, or too few windows.

**Likely cause**: The Solar file contains a header, strings, blank columns, or too few rows.

**Fix**:
- Keep the file as raw comma-separated floats with no header line.
- Remove any nonnumeric tokens.
- Add enough rows for the requested `seq_len` and `pred_len`.

## M4 missing cache files
**Symptom**: `M4-info.csv` not found, or the `.npz` archive cannot be opened.

**Likely cause**: The M4 directory is incomplete or the file names are different from the loader contract.

**Fix**:
- Provide `M4-info.csv`, `training.npz`, and `test.npz` in the same root directory.
- Check that `M4-info.csv` includes `M4id`, `SP`, `Frequency`, and `Horizon`.
- Verify that the requested seasonal pattern exists in the `SP` column.

## Anomaly file-name mismatch
**Symptom**: The anomaly loader reads the wrong columns, labels do not align, or a split file is missing.

**Likely cause**: The anomaly dataset does not match the expected file naming convention.

**Fix**:
- PSM-style CSVs need `train.csv`, `test.csv`, and `test_label.csv`.
- MSL / SMAP / SMD need `*_train.npy`, `*_test.npy`, and `*_test_label.npy`.
- SWAT uses `swat_train2.csv` and `swat2.csv`, with the label in the last test column.
- Make sure train/test/label row counts line up.

## Validation script advice
- Run the bundled validator with `--help` first.
- Use the smallest possible fixture that reproduces the layout problem.
- If a split is valid but windowing still fails, the issue is usually row count rather than file shape.
