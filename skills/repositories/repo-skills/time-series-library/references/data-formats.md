# Data Formats and Loader Behavior

TSLib loaders prefer local files when the expected files exist. If a local file is missing, several loaders attempt Hugging Face dataset downloads from `thuml/Time-Series-Library`. Avoid accidental network calls by validating paths before running.

## Forecasting and imputation CSVs

For `--data ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, or `custom`, the CSV must contain a `date` column and numeric feature columns. `custom` also uses `--target` to move the target column to the end.

Minimal custom layout:

```csv
date,feat1,feat2,OT
2024-01-01 00:00:00,0.1,1.2,10.0
2024-01-01 01:00:00,0.2,1.1,10.4
```

Loader behavior:

- `features M`: all columns after `date` are input and output channels.
- `features S`: only `target` is used.
- `features MS`: all columns are inputs, only the last/target channel is evaluated after slicing.
- Data is split chronologically: `custom` uses 70% train, 10% validation, 20% test after accounting for `seq_len`.
- ETT loaders use fixed benchmark split boundaries and expect enough rows for the official ranges.
- `freq` controls time features when `embed=timeF`.

## M4 short-term data

Use `--data m4 --root_path ./dataset/m4 --seasonal_patterns <Yearly|Quarterly|Monthly|Weekly|Daily|Hourly>`. The loader expects:

```text
M4-info.csv
training.npz
test.npz
submission-Naive2.csv  # needed for final M4Summary evaluation
```

If the triplet is missing, helper code may fetch files from the Hub. M4 training changes `seq_len`, `label_len`, and `pred_len` internally from the selected seasonal pattern.

## Anomaly detection data

Use `--task_name anomaly_detection` with `--data PSM`, `MSL`, `SMAP`, `SMD`, or `SWAT`.

Expected local files:

| `--data` | Required files |
| --- | --- |
| `PSM` | `train.csv`, `test.csv`, `test_label.csv` |
| `MSL` | `MSL_train.npy`, `MSL_test.npy`, `MSL_test_label.npy` |
| `SMAP` | `SMAP_train.npy`, `SMAP_test.npy`, `SMAP_test_label.npy` |
| `SMD` | `SMD_train.npy`, `SMD_test.npy`, `SMD_test_label.npy` |
| `SWAT` | `swat_train2.csv`, `swat2.csv` with label in the last test column |

The loaders standardize on training data and create sliding windows of length `seq_len`. Labels are used in `test()` for threshold evaluation and event-level adjustment.

## UEA classification data

Use `--task_name classification --data UEA --model_id <DatasetName> --root_path ./dataset/<DatasetName>/`. The loader expects:

```text
<DatasetName>_TRAIN.ts
<DatasetName>_TEST.ts
```

If local files are missing, it attempts to download the matching files from the Hub. The loader uses `sktime.datasets.load_from_tsfile_to_dataframe`, interpolates missing values, normalizes all rows, pads variable-length sequences through `collate_fn`, and derives `num_class` from categorical labels.

## Dataset validation strategy

Before a full command:

```bash
python sub-skills/data-and-cli/scripts/validate_tslib_data.py \
  --task long_term_forecast --data custom --root-path ./dataset/tiny-custom --data-path tiny.csv --target OT
```

This catches missing local files and common column/layout mistakes without running training or triggering downloads.

## Tiny fixtures

Use `scripts/create_tiny_tslib_dataset.py` to create a local CSV for smoke tests. It is not a benchmark dataset and should not be used for accuracy claims.
