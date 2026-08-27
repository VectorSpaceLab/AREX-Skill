# Data Layout

## Purpose

Read this when a workflow fails because a CSV, dataset directory, or generated
artifact is missing or named incorrectly.

## Shared forecasting CSV layout

The root benchmark routes and the FEDformer route both use CSV files with a
`date` column plus one or more feature columns.

Common files include:

- `ETTh1.csv`
- `ETTh2.csv`
- `ETTm1.csv`
- `ETTm2.csv`
- `exchange_rate.csv`
- `electricity.csv`
- `traffic.csv`
- `weather.csv`
- `national_illness.csv`
- custom CSVs supplied by the user

Typical root data root: `dataset/`.

### Column rules

- `date` must exist.
- For `features=M`, all non-`date` columns are used as model inputs and outputs.
- For `features=S` or `features=MS`, the selected `--target` column must exist,
  commonly `OT`.
- `custom` datasets in the root workflow use a 70/10/20 train/val/test split.
- The ETT loaders use fixed borders and expect the full benchmark CSVs, not a
  tiny synthetic file.

## Pyraformer data layout

The Pyraformer route creates and uses its own `Pyraformer/data/` tree during preprocessing. A fresh checkout may not contain that directory yet.

Common files and directories:

- `Pyraformer/data/ETT/`
- `Pyraformer/data/elect/`
- `Pyraformer/data/flow/`
- `Pyraformer/data/wind/`
- `Pyraformer/data/LD2011_2014.txt`
- `Pyraformer/data/synthetic.npy`
- `Pyraformer/models/LongRange/`
- `Pyraformer/models/SingleStep/`

The Pyraformer preprocessors generate `.npy` windows plus normalization values
under the relevant `Pyraformer/data/<name>/` directory.

## Generated artifacts

The repo writes run artifacts relative to the process working directory unless a
wrapper script redirects them:

- `checkpoints/`
- `results/`
- `test_results/`
- `logs/`
- `weights_plot/`
- `models/LongRange/`
- `models/SingleStep/`

## Quick checks

Use the bundled data-layout helper when a path or column looks wrong:

```bash
python scripts/check_data_layout.py --kind root --data-root dataset --data-path exchange_rate.csv --target OT
```

For Pyraformer paths:

```bash
python scripts/check_data_layout.py --kind pyraformer
```

If the helper reports a missing file, start by fixing the path, not the model
settings.
