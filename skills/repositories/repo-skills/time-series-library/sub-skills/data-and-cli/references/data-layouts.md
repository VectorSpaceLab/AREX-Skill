# Data Layouts for TSLib Commands

Use this reference before running `python run.py ...` with user-provided data.

## Forecasting and imputation CSVs

For `--data custom`, `ETTh1`, `ETTh2`, `ETTm1`, or `ETTm2`, TSLib expects a CSV containing `date` plus numeric feature columns.

```csv
date,feat1,feat2,OT
2024-01-01 00:00:00,0.1,1.2,10.0
2024-01-01 01:00:00,0.2,1.1,10.4
```

Flag interactions:

- `--root_path` is the directory containing the CSV.
- `--data_path` is the CSV filename.
- `--target` is used for `features S` and `features MS`; default is `OT`.
- `--features M` uses all non-date columns as inputs and outputs.
- `--features S` uses only the target column.
- `--features MS` uses all non-date columns as inputs but evaluates/predicts the target channel.
- `--freq` must match the timestamp granularity when `--embed timeF` is active.

For `custom`, TSLib chronologically splits rows into train/validation/test. Make sure the file has enough rows for `seq_len + pred_len` in each split.

## M4 short-term forecasting

For `--task_name short_term_forecast --data m4`, use:

```text
<root_path>/
  M4-info.csv
  training.npz
  test.npz
  submission-Naive2.csv  # needed for final averaged evaluation
```

`--seasonal_patterns` must be one of `Yearly`, `Quarterly`, `Monthly`, `Weekly`, `Daily`, or `Hourly`. The short-term experiment adjusts `seq_len`, `label_len`, and `pred_len` from this pattern.

## Anomaly detection folders

| `--data` | Required local files |
| --- | --- |
| `PSM` | `train.csv`, `test.csv`, `test_label.csv` |
| `MSL` | `MSL_train.npy`, `MSL_test.npy`, `MSL_test_label.npy` |
| `SMAP` | `SMAP_train.npy`, `SMAP_test.npy`, `SMAP_test_label.npy` |
| `SMD` | `SMD_train.npy`, `SMD_test.npy`, `SMD_test_label.npy` |
| `SWAT` | `swat_train2.csv`, `swat2.csv`; the last column of `swat2.csv` is treated as labels |

These loaders create sliding windows of length `seq_len`; labels are evaluated in `test()` after reconstruction-threshold scoring.

## UEA classification folders

For `--task_name classification --data UEA`, set `--model_id` to the dataset name and place:

```text
<root_path>/
  <DatasetName>_TRAIN.ts
  <DatasetName>_TEST.ts
```

The loader uses `sktime` to parse `.ts` files, converts categorical labels to class ids, interpolates missing values, normalizes rows, and pads variable-length sequences in the collate function.

## Local-vs-Hub fallback

If expected local files are missing, loaders for ETT/custom, M4, anomaly datasets, and UEA can attempt to read from the Hugging Face dataset `thuml/Time-Series-Library`. This is convenient for benchmarks but confusing in offline tasks. Validate local files first when the task is about user-provided data.
