# Preprocessing guide

`prepare_pyraformer_data.py` bundles the source preprocessing logic into one route-friendly helper. The helper keeps the source file naming, but makes the input and output locations explicit.

## Electricity preprocessing

Source behavior:

- reads `LD2011_2014.txt`
- resamples to hourly resolution
- fills missing values with zero
- filters series by their first non-zero position
- builds weekday / hour / month covariates
- normalizes each training window by its mean amplitude proxy
- writes both data arrays and label arrays

Typical output:

- `train_data_elect.npy`
- `train_v_elect.npy`
- `train_label_elect.npy`
- `test_data_elect.npy`
- `test_v_elect.npy`
- `test_label_elect.npy`

The source defaults use a `window_size` of 192 and a `stride_size` of 24.

## Flow preprocessing

Source behavior:

- reads the app-flow CSV
- groups rows by `app_name` and `zone`
- sorts each group by time
- keeps a series only if it is long enough and not too sparse
- adds weekday / hour / month covariates
- splits each sequence into training and testing windows
- normalizes each window by its mean amplitude proxy

Typical output:

- `train_data_flow.npy`
- `train_v_flow.npy`
- `test_data_flow.npy`
- `test_v_flow.npy`

The flow helper does not write separate label files; the single-step loader derives labels from the saved data windows.

## Wind preprocessing

Source behavior:

- reads the wind CSV
- transposes the raw matrix into the expected sequence layout
- builds weekday / hour / month covariates from a fixed start date
- splits each sequence into windows
- normalizes each window by its mean amplitude proxy
- filters out windows without positive history in the source `normalize` step

Typical output:

- `train_data_wind.npy`
- `train_v_wind.npy`
- `test_data_wind.npy`
- `test_v_wind.npy`

Like flow, wind does not write a separate label file in the preprocessing step.

## Synthetic generation

Source behavior:

- builds 60 mixed sinusoidal sequences by default
- uses periods of 24, 168, and 720 steps
- adds covariance-shaped Gaussian noise
- stores the result as one `.npy` array with the target series, covariates, and sequence id

Typical output:

- `data/synthetic.npy`

The source `simulate_sin.py` also contains an FBM test helper, but the default synthetic generator does not depend on it.

## Practical notes

- Use the preprocessing helper before any single-step run.
- Keep the generated files under the dataset directory that matches the `-data_path` argument.
- If you want deterministic synthetic output, set a seed before generating.
