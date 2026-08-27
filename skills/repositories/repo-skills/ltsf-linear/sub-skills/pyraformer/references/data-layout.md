# Data layout

This sub-skill needs two different layouts:

- the benchmark CSV layout for long-range forecasting, and
- the preprocessed `.npy` layout for the single-step route.

## Long-range CSV files

The long-range source scripts read benchmark CSV files from a root directory and a dataset-specific filename.

Common filenames used by the upstream scripts are:

- `ETTh1.csv`
- `ETTh2.csv`
- `ETTm1.csv`
- `ETTm2.csv`
- `electricity.csv`
- `exchange_rate.csv`
- `traffic.csv`
- `weather.csv`
- `national_illness.csv`

The source code expects the benchmark CSVs to contain the same column structure used by the original LTSF benchmark. For custom data, keep the time column and feature columns in the shape expected by the dataset key you choose.

## Single-step preprocessed files

The single-step route consumes a directory that contains the preprocessed outputs from the electricity, flow, or wind data-prep helper.

### Electricity layout

Expected files in `data/elect/`:

- `train_data_elect.npy`
- `train_v_elect.npy`
- `train_label_elect.npy`
- `test_data_elect.npy`
- `test_v_elect.npy`
- `test_label_elect.npy`

### Flow layout

Expected files in `data/flow/`:

- `train_data_flow.npy`
- `train_v_flow.npy`
- `test_data_flow.npy`
- `test_v_flow.npy`

### Wind layout

Expected files in `data/wind/`:

- `train_data_wind.npy`
- `train_v_wind.npy`
- `test_data_wind.npy`
- `test_v_wind.npy`

The flow and wind loaders derive labels from the stored data arrays, so the preprocessing step does not write separate `label` files for those datasets.

## Synthetic layout

- `data/synthetic.npy`

## Checkpoint layout

The source evaluation paths are fixed by route and key:

- Long-range: `models/LongRange/<data>/<predict_step>/best_iter<i>.pth`
- Single-step: `models/SingleStep/<dataset>/best_model.pth`

## Layout checks to remember

- Long-range runs need the CSV files and the right `root_path` / `data_path` combination.
- Single-step runs need the matching preprocessed directory in `-data_path`.
- Synthetic runs need only `data/synthetic.npy` unless you are regenerating it.
- If a path looks right but the run still fails, compare the dataset key against the file prefix in the file tree.
