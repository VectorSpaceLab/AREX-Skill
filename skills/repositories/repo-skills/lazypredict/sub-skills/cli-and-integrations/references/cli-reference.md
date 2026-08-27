# CLI Reference

## Command and flags

Lazy Predict installs a console command named `lazypredict`. Installed CLI help
verified these options:

```text
--task [classification|regression]
--input PATH
--target TEXT
--test-size FLOAT
--random-state INTEGER
--version
--help
```

If any of `--task`, `--input`, or `--target` is missing, the command prints a
short usage prompt and exits successfully without fitting models.

## Classification CSV

```bash
lazypredict --task classification --input data.csv --target label
```

The CSV must contain the target column. All other columns are passed as features
and split with `sklearn.model_selection.train_test_split` using `--test-size`
and `--random-state`.

## Regression CSV

```bash
lazypredict --task regression --input data.csv --target price --test-size 0.2
```

The CLI prints the Lazy Predict score DataFrame as text. Use the Python API when
the user needs predictions, fitted model objects, categorical encoder choices,
custom metrics, cross-validation, model subsets, MLflow control, or persistence.

## Limitations

- No CLI flag selects a subset of models or sets `max_models`; all default
  models for the task may be attempted.
- No CLI flag sets `timeout`, `categorical_encoder`, `cv`, `predictions`,
  `custom_metric`, `tune`, or `use_gpu`.
- No time-series CLI is exposed. Use `LazyForecaster` from Python.
- The CLI expects a local CSV file and does not download datasets.

## Bundled smoke helper

```bash
python scripts/smoke_cli.py --task classification
python scripts/smoke_cli.py --task regression --skip-fit
```

The helper uses Click's in-process runner and temporary toy CSVs. This avoids
PATH confusion while still testing the package's CLI command object. If the
installed `lazypredict` executable is on `PATH`, the helper also checks
`--version`.
