# Ray Train And Tune API Reference

This reference summarizes the Train and Tune APIs most often needed for training and tuning tasks. Signatures and fields are based on the inspected Ray package surface and current repository docs, distilled into self-contained guidance.

## Package Surface

- Import Train with `from ray import train` or targeted trainer modules such as `ray.train.torch` when the framework package is installed.
- Import Tune with `from ray import tune`.
- Prefer `pip install "ray[train]"` for Train and `pip install "ray[tune]"` for Tune. Add `torch`, `tensorflow`, `xgboost`, `lightgbm`, `optuna`, `hyperopt`, or cloud filesystem packages only when the selected workflow needs them.
- Console scripts include `ray` and `tune`, but programmatic Train/Tune jobs should usually be launched from Python.

## Responsibility Split

| Need | Primary API | Notes |
| --- | --- | --- |
| Distributed training workers | Ray Train | A trainer or training driver owns workers, scaling, checkpoints, and training-specific fault tolerance. |
| Hyperparameter search and trial orchestration | Ray Tune | Tune samples configs, schedules trials, limits concurrency, and returns a `ResultGrid`. |
| Train+Tune integration | Tune outer loop, Train inner loop | A Tune trainable can create and run a Train trainer per sampled config. Keep the Tune trial driver lightweight and reserve resources for inner Train workers. |
| Dataset ingestion and transforms | Ray Data | Build datasets with the Data sub-skill, then pass them into Train/Tune workflows explicitly. |
| Serving a trained model | Ray Serve | After training, route deployment packaging and Serve applications to the Serve sub-skill. |

## Ray Train Core Objects

### `train.ScalingConfig`

```python
train.ScalingConfig(
    num_workers=1,
    use_gpu=False,
    resources_per_worker=None,
    placement_strategy="PACK",
    accelerator_type=None,
)
```

Key fields:

- `num_workers`: number of training workers. Current Train V2 also accepts an elastic `(min_workers, max_workers)` tuple.
- `use_gpu`: reserves one GPU per worker unless `resources_per_worker` overrides GPU count.
- `resources_per_worker`: per-worker resource map; Train resource keys use Ray logical resource names such as `"CPU"` and `"GPU"`.
- `placement_strategy`: placement group strategy, commonly `"PACK"`, `"SPREAD"`, or `"STRICT_SPREAD"` depending on locality/failure-isolation needs.
- `accelerator_type`: asks Ray to place workers on nodes with a specific accelerator type when the cluster advertises accelerator resources.

Use this object for Train worker resources. Tune trial resources are specified separately with `tune.with_resources`.

### `train.RunConfig`

```python
train.RunConfig(
    name=None,
    storage_path=None,
    storage_filesystem=None,
    failure_config=None,
    checkpoint_config=None,
    callbacks=None,
    worker_runtime_env=None,
)
```

Key fields:

- `name`: experiment/run directory name under `storage_path`.
- `storage_path`: persistent output root. Use a shared filesystem or cloud URI for multi-node checkpointing.
- `storage_filesystem`: custom `pyarrow.fs.FileSystem`; when supplied, `storage_path` should be the filesystem path form expected by that filesystem.
- `failure_config`: Train-level retry/failure policy.
- `checkpoint_config`: checkpoint retention and score policy.
- `callbacks`: Train callbacks such as reporting or framework integrations.
- `worker_runtime_env`: runtime environment applied to Train workers.

### `train.CheckpointConfig`

```python
train.CheckpointConfig(
    num_to_keep=None,
    checkpoint_score_attribute=None,
    checkpoint_score_order="max",
)
```

Use this with `RunConfig(checkpoint_config=...)` to retain only the best or most recent checkpoints. `checkpoint_score_attribute` must match a metric key reported with the checkpoint, and `checkpoint_score_order` must match whether larger or smaller values are better.

### `train.FailureConfig`

```python
train.FailureConfig(max_failures=0, controller_failure_limit=-1)
```

Use this to configure Train run retry behavior. Keep Train failure handling separate from Tune trial failure handling when Train is launched inside Tune.

### `train.report`

```python
train.report(
    metrics: dict,
    checkpoint=None,
    checkpoint_dir_name=None,
    checkpoint_upload_mode=...,  # synchronous by default
    delete_local_checkpoint_after_upload=None,
    checkpoint_upload_fn=None,
    validation=False,
)
```

Rules:

- Report plain JSON-like metric values that downstream tooling can serialize.
- To checkpoint, first write a local checkpoint directory, wrap it with the Train `Checkpoint` API for the installed Ray version, then pass it as `checkpoint=...`.
- In data-parallel training where each worker has a complete model copy, usually report a checkpoint from one rank only to avoid redundant uploads.
- In sharded/model-parallel training, each worker can report a shard, but filenames must not collide unless identical contents are intended.

## Ray Tune Core Objects

### `tune.Tuner`

```python
tune.Tuner(
    trainable,
    param_space=None,
    tune_config=None,
    run_config=None,
)
```

`Tuner.fit()` launches the experiment and returns a `tune.ResultGrid`. The `trainable` may be a function, a `tune.Trainable` subclass, a registered trainable name, or supported trainer object. For current Train+Tune workflows, prefer a function trainable that launches Train inside the trial rather than relying on deprecated direct trainer tuning patterns.

### `tune.TuneConfig`

```python
tune.TuneConfig(
    metric=None,
    mode=None,
    search_alg=None,
    scheduler=None,
    num_samples=1,
    max_concurrent_trials=None,
    time_budget_s=None,
    reuse_actors=False,
)
```

Key fields:

- `metric`: reported metric key to optimize.
- `mode`: `"min"` or `"max"`; must match the metric objective.
- `search_alg`: optional Tune search algorithm such as Optuna, HyperOpt, BayesOpt, or a custom searcher.
- `scheduler`: optional trial scheduler such as FIFO, ASHA/AsyncHyperBand, HyperBand, MedianStopping, or PBT.
- `num_samples`: random samples; if `grid_search` is present, the grid is repeated `num_samples` times.
- `max_concurrent_trials`: hard cap on concurrently running trials; useful when trials launch Train workers or nested Ray work.
- `time_budget_s`: experiment-level wall-clock budget.
- `reuse_actors`: can reduce actor startup overhead when trials have the same resource requirements.

### `tune.RunConfig`

```python
tune.RunConfig(
    name=None,
    storage_path=None,
    storage_filesystem=None,
    failure_config=None,
    checkpoint_config=None,
    sync_config=None,
    verbose=None,
    stop=None,
    callbacks=None,
    progress_reporter=None,
    log_to_file=False,
)
```

Use Tune `RunConfig` for trial output storage, stop conditions, Tune callbacks, Tune checkpoint retention, and trial-level fault tolerance. It is distinct from Train `RunConfig`, even though many fields share names.

### Search Space Helpers

```python
tune.grid_search([1, 2, 3])
tune.choice(["small", "large"])
tune.uniform(0.0, 1.0)
tune.sample_from(lambda config: config["base"] * 2)
```

Guidelines:

- Put search spaces in `Tuner(param_space=...)`.
- Use constants for fixed parameters.
- `grid_search` evaluates every listed value and combines with other grids by Cartesian product.
- `num_samples` repeats random samples and repeats grids when grids are present.
- Some third-party search algorithms do not support Python lambdas, conditional spaces, or grid search in Tune's native format.
- Avoid embedding large objects in `param_space`; load them inside the trainable or pass references with APIs intended for large parameters.

### `tune.report`

```python
tune.report(metrics: dict, *, checkpoint=None)
```

Use `tune.report` inside a Tune trainable. The reported metric keys are what `TuneConfig(metric=...)`, schedulers, search algorithms, and `ResultGrid.get_best_result()` consume. The optional `checkpoint` is for Tune trainable state; if a Ray Train run inside the trial already reports worker checkpoints, do not duplicate checkpoints at the Tune driver unless the driver owns additional state.

### `tune.with_resources`

```python
tune.with_resources(trainable, {"cpu": 1, "gpu": 0})
```

Use this wrapper to tell Tune how many logical resources each trial driver needs. For trainables that start additional Ray tasks, actors, Ray Data jobs, or Ray Train workers, reserve enough resources with a placement group factory or keep `max_concurrent_trials` low enough to leave resources for nested work.

### Schedulers And Search Algorithms

```python
from ray.tune.schedulers import AsyncHyperBandScheduler

scheduler = AsyncHyperBandScheduler(metric="loss", mode="min", max_t=10, grace_period=1)
```

Common scheduler choices:

- FIFO/default: simplest, no early stopping.
- AsyncHyperBand/ASHA: early-stops poor trials based on reported metrics and training iterations.
- MedianStopping: stops trials underperforming the median.
- PopulationBasedTraining: mutates configs and checkpoints across trials; requires compatible trainables/checkpointing.

Search algorithms propose configurations; schedulers decide how running trials are allocated or stopped. Use `metric` and `mode` consistently across both when required.

## ResultGrid And Result Analysis

`Tuner.fit()` returns a `ResultGrid`:

```python
results = tuner.fit()
best = results.get_best_result(metric="loss", mode="min")
print(best.config)
print(best.metrics)
print(best.checkpoint)
df = results.get_dataframe()
```

Important methods/properties:

- `get_best_result(metric=None, mode=None, scope="last", filter_nan_and_inf=True)`: returns the best `Result`. If `metric`/`mode` were not set in `TuneConfig`, pass them here.
- `get_dataframe(filter_metric=None, filter_mode=None)`: returns trial results as a pandas DataFrame. Use filters to select each trial's best metric value rather than final value.
- `experiment_path`: path to the experiment directory on persistent storage.
- `errors`, `num_errors`, `num_terminated`: inspect trial failures and completion status.
- Iteration and indexing expose per-trial `Result` objects.

## Object Relationship Cheat Sheet

```text
Tuner
  trainable: function/class/trainer driver
  param_space: search dimensions and constants
  tune_config: search/scheduler/concurrency/metric/mode
  run_config: output/checkpoint/failure/callback/logging settings
  fit() -> ResultGrid -> Result objects

Train driver or trainer
  scaling_config: worker count/resources/placement
  run_config: Train output/checkpoint/failure/callback/runtime settings
  train_loop_per_worker: calls train.report(metrics, checkpoint=...)
```

Keep configuration ownership explicit: Tune controls trial orchestration and result selection; Train controls distributed worker execution and Train checkpoints.
