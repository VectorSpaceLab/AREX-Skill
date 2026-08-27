# Tuning and Distributed Workflows

## Purpose

Read this when the user wants Auto* model search, Ray/Optuna configuration, or
Spark-based distributed training and inference.

## Public API anchors

- `BaseAuto(cls_model, h, loss, valid_loss, config, ...)`
- `AutoNHITS(...)`, `AutoMLP(...)`, and the other `Auto*` wrappers
- `RayOptions(run_config=None, scheduler=None, cpus=None, gpus=None)`
- `OptunaOptions(study_kwargs=None, create_study_kwargs=None)`
- `DistributedConfig(partitions_path, num_nodes, devices)`

## Choosing a backend

| Need | Suggested path | Notes |
| --- | --- | --- |
| Tiny local search | Ray or Optuna with `num_samples=1` | Good for API validation and small experiments. |
| Simple parameter search | Optuna | Good when the search space is explicit and lightweight. |
| Ray-based parallel search | Ray | Use `RayOptions` to control CPUs/GPUs and run config. |
| Spark distributed fit / predict | `DistributedConfig` + Spark DataFrames | Static and local scalers are not supported in the distributed path. |

## What to remember from source and tests

- `BaseAuto` validates that the wrapped model config exposes the keys the model
  needs.
- `Auto*` wrappers translate `input_size_multiplier` into `input_size` in the
  normalized config path.
- Ray GPU allocation should be conservative; a single GPU per trial is the
  common safe default.
- `use_fitted=True` on cross-validation is a special path and has extra
  restrictions.
- Distributed Spark paths disable historic and static scaling.

## Minimal safe local example

```python
from neuralforecast.auto import AutoMLP
from neuralforecast.utils import generate_series
from neuralforecast.tsdataset import TimeSeriesDataset

series = generate_series(n_series=2, min_length=30, max_length=30, equal_ends=True)
dataset, *_ = TimeSeriesDataset.from_df(series)

config = AutoMLP.default_config.copy()
config.update({"h": 4, "input_size_multiplier": 1, "max_steps": 1, "val_check_steps": 1})
auto = AutoMLP(h=4, config=config, num_samples=1, cpus=1)
```

Use a tiny config like this when the goal is only to prove the search wrapper
parses correctly.

## Spark/distributed reminders

- Pass `distributed_config` only when using Spark DataFrames or file-backed
  distributed workflows.
- Set `partitions_path` to a writable location.
- Do not expect local-scaler behavior in the distributed path.
- If the user only has pandas data, the distributed path is probably not the
  right choice.

## Read next

- `api-reference.md` for signatures.
- `data-formats.md` for dataframe and static-data constraints.
- `troubleshooting.md` for backend, resource, and configuration errors.
