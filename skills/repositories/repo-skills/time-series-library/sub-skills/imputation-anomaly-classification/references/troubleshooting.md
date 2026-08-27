# Imputation, Anomaly Detection, and Classification Troubleshooting

## Imputation mask results look wrong

Symptoms:

- Metrics change a lot across runs.
- Filled PDF plots look noisy.
- `mask.npy` seems inverted.

Checks and fixes:

- `mask == 0` marks values hidden from the model and used for metric calculation.
- Keep the random seed stable when comparing experiments; `run.py` seeds Python, NumPy, and Torch at startup.
- Compare runs only when `--mask_rate`, model, window length, and data split are the same.
- On tiny synthetic data, use imputation only to validate code paths, not model quality.

## Imputation tensor shape mismatch

Likely causes:

- `--enc_in`, `--dec_in`, or `--c_out` does not match the number of non-date CSV columns.
- `--features MS` was used but the target column or channel counts were copied from an `M` benchmark script.
- The selected model does not implement the imputation forward path.

Fixes:

- Validate the CSV with `../data-and-cli/scripts/validate_tslib_data.py`.
- Start with `--model TimesNet`, which is the README imputation example.
- Set `--label_len 0 --pred_len 0` for standard imputation scripts.

## Anomaly data files or labels are missing

Symptoms:

- Loader starts a Hub download.
- File-not-found or shape errors appear in `PSMSegLoader`, `MSLSegLoader`, `SMAPSegLoader`, `SMDSegLoader`, or `SWATSegLoader`.

Fixes:

- Confirm the exact local files listed in `../data-and-cli/references/data-layouts.md`.
- For PSM CSVs, labels are read from `test_label.csv` after the first column.
- For SWAT, the last column of `swat2.csv` is treated as labels.
- Use `--num_workers 0` while diagnosing file and shape errors.

## Anomaly metrics are unstable or undefined

Likely causes:

- Tiny test data has too few anomaly events.
- `--anomaly_ratio` does not match the dataset's expected anomaly prior.
- Reconstruction scores are almost constant, causing poor percentile separation.

Fixes:

- Use official dataset-scale data for metric claims.
- Treat tiny fixtures as plumbing checks only.
- Inspect stdout threshold and the lengths of train/test loaders.
- Explain that TSLib applies event-level adjustment after thresholding, so point-level raw scores and final metrics can differ.

## UEA classification files are not found

Symptoms:

- Loader tries Hugging Face unexpectedly.
- `BuilderConfig` or `.ts` parsing errors mention the dataset name.

Fixes:

- Set `--model_id <DatasetName>` exactly matching the local file prefix.
- Put `<DatasetName>_TRAIN.ts` and `<DatasetName>_TEST.ts` under `--root_path`.
- Do not use `--data_path`; UEA resolution ignores it.
- Install `sktime` for `.ts` parsing.

## Classification model dimensions seem ignored

This is expected: `Exp_Classification` loads TRAIN and TEST data before model creation and sets `seq_len`, `pred_len`, `enc_in`, and `num_class` from the loaded data. Avoid forcing forecasting-style channel flags onto classification commands.

## Augmentation fails

- Use `--augmentation_ratio` with one augmentation flag first.
- DTW-based augmentations (`spawner`, `dtwwarp`, `shapedtwwarp`, `wdba`, `discdtw`, `discsdtw`) can be slower and have class/sample assumptions.
- Some augmentations are designed primarily for classification-style arrays; validate shapes before large runs.
