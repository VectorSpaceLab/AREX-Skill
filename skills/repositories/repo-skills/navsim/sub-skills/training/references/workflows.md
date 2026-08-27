# Training workflows

This reference distills the NAVSIM v2 training runner and its two maintained
training command templates. The commands below are intentionally examples for
an explicitly approved run; none should be launched as part of skill loading,
planning, or diagnosis.

## 1. Establish the training identity

Record all of the following before touching data:

- agent config: `ego_status_mlp_agent`, `transfuser_agent`, or a custom
  `_target_` implementing the learned-agent contract;
- trajectory sampling: the baseline configs use a 4-second horizon and
  `interval_length=0.5`, producing 8 future poses with 3 values each;
- feature and target builders, including each builder's `get_unique_name()`;
- training and validation log lists;
- selected `train_test_split` group and its underlying `data_split`;
- cache root, output root, precision, accelerator, devices, and loader workers.

Treat a cache made for a different TransFuser `latent` setting or different
trajectory sampling as a different cache, even when the directory name is the
same. The builder file stem alone does not encode every constructor option.

## 2. Choose a data path

There are two safe planning choices:

- **SceneLoader path** (`use_cache_without_dataset=false`): the runner builds
  filtered train and validation `SceneLoader` instances. `Dataset` can compute
  missing features/targets on construction when `cache_path` is set. This is
  convenient for a tiny smoke fixture but is a poor default for a full dataset.
- **Cache-only path** (`use_cache_without_dataset=true`): the runner skips
  `SceneLoader` and uses `CacheOnlyDataset`. It ignores the scene filter and
  selects cache directories using `train_logs` and `val_logs`; every requested
  builder file must already exist. Use this only after a complete,
  split-compatible cache has been prepared.

For a large dataset, plan a separate, explicitly approved caching phase with a
small worker configuration. The cache writer creates one gzip-pickle per
builder and token; it is not a benchmark and should not be conflated with
metric caching.

## 3. Exact Hydra patterns

The maintained baseline templates use the following override shape:

```bash
python -m navsim.planning.script.run_training \
  experiment_name=training_ego_mlp_agent \
  trainer.params.max_epochs=50 \
  train_test_split=navtrain
```

For TransFuser, the agent group is changed explicitly:

```bash
python -m navsim.planning.script.run_training \
  agent=transfuser_agent \
  experiment_name=training_transfuser_agent \
  train_test_split=navtrain
```

Useful planning overrides are exact dotted Hydra keys, for example:

```text
cache_path=<approved-cache-root>
use_cache_without_dataset=true
force_cache_computation=false
train_logs=[<train-log-a>,<train-log-b>]
val_logs=[<val-log-a>]
dataloader.params.batch_size=8
dataloader.params.num_workers=2
dataloader.params.pin_memory=true
trainer.params.accelerator=gpu
trainer.params.strategy=auto
trainer.params.devices=1
trainer.params.precision=16-mixed
trainer.params.max_epochs=1
```

`train_test_split=navtrain` selects a config group. It is not interchangeable
with the legacy-looking top-level `split` field in the default training YAML.
The runner reads `cfg.train_test_split.scene_filter`, `cfg.navsim_log_path`,
`cfg.original_sensor_path`, `cfg.train_logs`, and `cfg.val_logs`; inspect the
composed values rather than assuming a command-line name was consumed.
Always supply a non-empty `experiment_name`, because the shared evaluation
config interpolates the output directory from it.

## 4. Prepare a cache separately

When a full cache is required, the package provides a dataset-caching runner
that uses the selected agent's sensor config, builders, scene loader, and a
worker pool. A planned command has this shape, but must remain disabled until
logs, sensors, maps/synthetic inputs where relevant, disk budget, and overwrite
policy are approved:

```bash
python -m navsim.planning.script.run_dataset_caching \
  agent=ego_status_mlp_agent \
  train_test_split=navtrain \
  cache_path=<approved-cache-root> \
  force_cache_computation=true \
  worker=sequential
```

`worker=sequential` is the most conservative diagnostic choice. For a real
cache, select a bounded thread/process or Ray worker plan only after measuring
CPU, storage, and file-descriptor limits. This worker setting belongs to the
caching runner; the training runner uses `dataloader.params.num_workers` for
batch loading and does not instantiate the shared worker pool itself.

Do not use `force_cache_computation=true` as a routine cache refresh: it
recomputes all scene-loader tokens and overwrites builder files. With it false,
`Dataset` computes only tokens whose required builder files are missing.

## 5. Model and checkpoint handoff

`AgentLightningModule` owns the Lightning training/validation steps. It calls
`agent.forward(features)`, passes the result to `agent.compute_loss`, logs
`train/loss` or `val/loss`, and delegates optimizer construction to
`agent.get_optimizers()`. The trainer adds callbacks returned by the agent;
TransFuser's callback produces train/validation visualizations and therefore
needs a usable logger and sufficient batch samples.

During a normal training plan, leave `agent.checkpoint_path=null` unless the
agent implementation explicitly supports initialization from a prior model.
For later learned-agent loading, pass a real checkpoint with the agent override:

```text
agent=ego_status_mlp_agent
agent.checkpoint_path=<approved-checkpoint>
```

The learned baseline loaders expect a Lightning-style mapping with a
`state_dict`; they remove the `agent.` prefix before loading. Verify the
checkpoint's state keys and the exact agent/trajectory configuration before
using it. Do not claim a checkpoint is valid from its filename alone.

## 6. Safe planning checklist

1. Run `scripts/inspect_training_config.py` with the intended split and key
   overrides.
2. Confirm `train_logs` and `val_logs` are present in the selected cache when
   using cache-only mode.
3. Confirm every feature/target builder file exists for at least one synthetic
   sample if performing a tiny fixture check.
4. Confirm CUDA, precision, strategy, devices, batch size, and loader workers
   fit the host; lower them for a smoke plan.
5. Explicitly approve the data access and command before launching caching or
   training.
