# Ray Train And Tune Troubleshooting

Use this guide when a Train/Tune workload fails to import, hangs, reports no best result, loses checkpoints, or writes outputs somewhere unexpected.

## Missing Extras Or Optional Packages

Symptoms:

- `ModuleNotFoundError` for `ray.train`, `ray.tune`, framework trainers, search algorithms, or cloud filesystems.
- Trainer imports succeed, but framework-specific code fails for `torch`, `tensorflow`, `xgboost`, `lightgbm`, `pyarrow`, `fsspec`, `optuna`, `hyperopt`, or similar packages.

Fixes:

- Install the narrow extra first: `ray[train]` for Train, `ray[tune]` for Tune, `ray[data]` only for Data pipelines, and framework/search packages only when needed.
- Avoid `ray[all]` by default because it installs broad dependencies unrelated to the selected workflow.
- For cloud storage, install and configure the filesystem dependency required by the chosen URI or `pyarrow.fs.FileSystem`.
- Verify the basic API before running a large job: `python scripts/tune_train_smoke.py --check-imports`.

## Persistent Storage Problems

Symptoms:

- Train checkpoints work locally but fail on a multi-node cluster.
- Workers cannot upload checkpoints.
- Results appear under the head node only, or checkpoint paths are missing after cluster termination.
- Custom filesystem paths fail because the URI format is wrong.

Fixes:

- For multi-node Train checkpointing, use storage every worker can write to: object storage such as S3/GCS/Azure Blob, HDFS, or a shared filesystem mounted consistently on all nodes.
- Do not use head-node local storage as the checkpoint destination for multi-node Train jobs that report checkpoints.
- Set `RunConfig(storage_path=..., name=...)` on Train or Tune when output location must be predictable.
- When `storage_filesystem` is supplied, format `storage_path` for that filesystem. Custom filesystem integrations may expect a path without the URI protocol prefix.
- Keep credentials and networking consistent across all worker nodes; Train expects every checkpointing worker to reach the same storage location.

## Metric And Mode Mistakes

Symptoms:

- `ResultGrid.get_best_result()` raises that no metric or mode is provided.
- Schedulers do not stop bad trials.
- Best trial selection is wrong.
- Checkpoint retention does not keep the intended checkpoints.

Fixes:

- Ensure the trainable reports the exact key used by `TuneConfig(metric=...)`, scheduler configuration, and `get_best_result(metric=...)`.
- Set `mode="min"` for losses and `mode="max"` for accuracy/reward/score metrics.
- Pass `metric` and `mode` to `get_best_result` if they were not set in `TuneConfig`.
- For Train checkpoint retention, make `CheckpointConfig(checkpoint_score_attribute=...)` match a metric reported with the checkpoint.
- Inspect `results.get_dataframe()` to confirm the metric column exists and contains finite values.

## Tune Resource Deadlocks Or Hangs

Symptoms:

- Trials stay pending even though the cluster appears idle.
- Tune reports insufficient resources or repeatedly waits for placement groups.
- A trainable starts Ray Data, remote tasks, actors, or Train workers and then hangs.
- All CPUs are occupied by Tune trial actors, leaving none for nested work.

Fixes:

- Start with `max_concurrent_trials=1` and increase only after one trial completes.
- Wrap trainables with `tune.with_resources` so per-trial driver resources are explicit.
- Leave spare CPUs/GPUs for nested Ray work. If each trial launches Train workers, calculate concurrency from the worker resources, not from the lightweight Tune driver resources.
- For complex nested resources, use a Tune placement group factory instead of only `{"cpu": 1}`.
- Route low-level Ray resource and placement-group analysis to `../core-runtime/SKILL.md`.
- Route Ray Data block/concurrency tuning inside the trainable to `../data-pipelines/SKILL.md`.

## GPU Visibility And Allocation

Symptoms:

- GPU code inside a Tune trainable sees no GPUs.
- Multiple trials oversubscribe a GPU.
- Train workers fail to acquire GPU resources.

Fixes:

- For Tune trial GPU work, use `tune.with_resources(trainable, {"gpu": 1})`; Tune sets `CUDA_VISIBLE_DEVICES` according to the requested GPUs.
- For Train worker GPU work, set `train.ScalingConfig(use_gpu=True)` or explicit `resources_per_worker={"GPU": ...}` for the trainer workers.
- When Tune launches Train, remember there are two resource layers: Tune trial driver resources and Train worker resources.
- Use `max_concurrent_trials` to keep the number of simultaneous Train runs within cluster GPU capacity.
- If previous trials do not release GPU memory quickly, add framework cleanup and consider waiting for GPU memory before launching new trials.

## Checkpoint And Report Misuse

Symptoms:

- Metrics appear but checkpoints are missing.
- Checkpoint upload is slow or blocks training.
- Data-parallel training uploads duplicate checkpoints.
- Tune trial checkpoints duplicate Train checkpoints.

Fixes:

- For Train, write state to a local directory, create a Train checkpoint object, and pass it to `train.report(metrics, checkpoint=...)`.
- For Tune-only trainables, pass a Tune checkpoint to `tune.report(metrics, checkpoint=...)` when the trial itself owns resumable state.
- In standard data-parallel Train, checkpoint from one worker unless each worker owns a distinct shard.
- In sharded Train, avoid filename collisions across worker checkpoint directories unless files are intentionally identical.
- Configure `CheckpointConfig(num_to_keep=..., checkpoint_score_attribute=..., checkpoint_score_order=...)` with reported metric names.
- When Train is nested inside Tune, do not add a driver-level Tune checkpoint unless the driver has additional state not captured by Train.

## Output And Log Locations

Symptoms:

- Results are not where expected.
- TensorBoard or CSV/JSON logs are missing.
- `log_to_file=True` output is not synced to cloud.
- Distributed worker logs are not in the Tune trial stdout/stderr files.

Fixes:

- By default, Tune and Train write under a Ray results directory, commonly in the user's home directory. Set `RunConfig(storage_path=..., name=...)` for predictable paths.
- Tune writes each trial to a trial subdirectory under the experiment directory; `ResultGrid.experiment_path` points to the experiment root.
- Tune automatically logs trial results in TensorBoard/CSV/JSON formats when dependencies are available.
- `RunConfig(log_to_file=True)` captures Tune trainable stdout/stderr in the trial directory, but distributed Train worker logs are not part of that setting.
- If syncing outputs to cloud, verify whether custom artifacts and log files are included by the selected sync configuration.

## Search Space And Scheduler Incompatibility

Symptoms:

- A third-party search algorithm rejects `grid_search`, lambdas, or conditional spaces.
- Conditional parameters are not sampled as expected.
- `num_samples` creates more trials than expected.

Fixes:

- For basic Tune search, use native `tune.grid_search`, `tune.choice`, `tune.uniform`, and `tune.sample_from` in `param_space`.
- With third-party search algorithms, read the algorithm's supported search-space format and avoid unsupported Tune-native constructs.
- Remember that `num_samples` repeats random sampling and repeats an entire grid when a grid is present.
- Keep large objects out of `param_space`; load them inside the trainable or use parameter-passing APIs designed for large values.

## Train+Tune Integration Pitfalls

Symptoms:

- Directly tuning a trainer object emits deprecation or migration warnings.
- Tune trial drivers run, but Train workers wait forever.
- Tune callbacks do not see Train worker metrics.

Fixes:

- Prefer function-based Train+Tune integration: the Tune trainable receives a config, builds a Train trainer/driver, calls `trainer.fit()`, and reports a summary metric to Tune.
- Keep the Tune trial driver lightweight; reserve real training resources in `ScalingConfig`.
- Use Train callbacks for Train worker behavior and Tune callbacks in Tune `RunConfig(callbacks=...)` for outer experiment behavior.
- If a Tune callback depends on Train-reported metrics, propagate Train results back to Tune explicitly with an integration callback or a final `tune.report` from the trial driver.

## Quick Diagnostic Sequence

1. Run `python scripts/tune_train_smoke.py --check-imports` to verify imports and key signatures.
2. Run one deterministic trial with `max_concurrent_trials=1` and no scheduler.
3. Add `metric`/`mode`, then verify `ResultGrid.get_best_result()` and `get_dataframe()`.
4. Add checkpoints with local single-node storage.
5. Move to shared/cloud storage before multi-node checkpointing.
6. Add schedulers/search algorithms only after metrics and resources are correct.
7. Increase concurrency last, watching available CPUs/GPUs and nested Ray work.
