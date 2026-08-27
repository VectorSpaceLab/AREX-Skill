# Imputation, Anomaly Detection, and Classification Workflows

## Imputation

Use `--task_name imputation` with ETT/custom-style CSV data. Typical settings set `--label_len 0 --pred_len 0` because the model reconstructs missing values over the input window rather than forecasting future windows.

Key flags:

- `--mask_rate`: probability of masking each value. Examples use `0.125`, `0.25`, `0.375`, and `0.5`.
- `--seq_len`: reconstruction window length.
- `--features`, `--target`, `--enc_in`, `--dec_in`, `--c_out`: same channel rules as forecasting.
- `--model`: TimesNet is the README example; other models must implement imputation forward behavior.

Validation sequence:

1. Validate CSV local path and target column.
2. Run one epoch on CPU with tiny windows.
3. Inspect `results/<setting>/mask.npy` and metric output only after smoke succeeds.

## Anomaly detection

Use `--task_name anomaly_detection` with `--data PSM`, `MSL`, `SMAP`, `SMD`, or `SWAT`.

Key flags:

- `--seq_len`: sliding reconstruction window.
- `--pred_len 0`: anomaly detection reconstructs current windows.
- `--anomaly_ratio`: percentile prior used to choose the reconstruction-energy threshold.
- `--enc_in` and `--c_out`: channel counts for the anomaly dataset.

The experiment:

1. Trains reconstruction on train windows.
2. Computes train and test reconstruction energy.
3. Sets threshold at percentile `100 - anomaly_ratio` over combined train/test energy.
4. Converts test energy to binary predictions.
5. Applies event-level adjustment through `utils.tools.adjustment`.
6. Reports accuracy, precision, recall, and F-score.

Dataset-specific channel counts in scripts are evidence, not universal truth. Verify the actual local data when using a modified dataset.

## Classification

Use `--task_name classification --data UEA --model_id <DatasetName>`. The loader expects `<DatasetName>_TRAIN.ts` and `<DatasetName>_TEST.ts` under `--root_path` or attempts Hub fallback.

The classification experiment:

1. Loads TRAIN and TEST through the UEA loader.
2. Derives `seq_len` as the max train/test sequence length.
3. Derives `enc_in` from feature dimensions.
4. Derives `num_class` from labels.
5. Trains with cross-entropy and reports accuracy.

Do not set `--data_path`; UEA file resolution comes from `--model_id` and split names.

## Augmentation in these tasks

`run.py` exposes augmentation flags such as `--jitter`, `--scaling`, `--permutation`, `--magwarp`, `--timewarp`, `--windowslice`, `--windowwarp`, `--rotation`, `--spawner`, `--dtwwarp`, `--shapedtwwarp`, `--wdba`, `--discdtw`, and `--discsdtw`. Use them with `--augmentation_ratio <n>` when the selected data loader/task supports augmentation. Start with one augmentation method and inspect data shapes before combining several.
