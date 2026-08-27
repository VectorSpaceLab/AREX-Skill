# Training and preprocessing troubleshooting

Use the smallest reproducible scope: one deterministic scenario or mock, one
worker, one batch, and FP32. Preserve the resolved Hydra config, builder names,
cache root, package versions, and first failing tensor before changing multiple
variables.

## Recovery order

1. Run `scripts/validate_training_config.py` and fix YAML, required-section,
   type, and unresolved-value findings.
2. Compose one coherent `training_*_model` fragment with
   `worker=sequential`, `data_loader.params.num_workers=0`, a tiny scenario
   filter, `drop_last=false`, and precision 32.
3. Construct the wrapper and datamodule, call `setup("fit")`, and obtain one
   train/validation batch. Do not call `trainer.fit` first.
4. Compute one sample with `FeaturePreprocessor`; print feature/target unique
   names, validity, dtype, and shape. Then perform a cache round trip.
5. Run one bounded `fast_dev_run` with `terminate_on_nan=true`.
6. Only after this works, expand cache/scenario count, restore workers and
   augmentation, and consider CUDA/FP16 or distributed execution.

## YAML and Hydra failures

### Missing required sections or unresolved `???`

The safe validator is intentionally not a Hydra composer. Validate a materialized
standalone training document with top-level `training`, `model`, `cache`, and
`worker` sections before execution. Source fragments such as `default_training`
may rely on `defaults` and therefore are not complete standalone documents.
Compose the intended experiment first when using source fragments. `default_training`
also intentionally leaves `model`, `splitter`, `objective`,
`training_metric`, `objective_aggregate_mode`, and `py_func` unresolved until a
fragment/override supplies them.

A model config must have a compatible Hydra `_target_` and constructor values.
The safe validator reports target strings but never imports or instantiates them;
let `build_torch_module_wrapper` perform the real type check in a compatible
runtime.

### Unknown override or list parsing

Use `+training=training_vector_model` when adding the experiment group used by
`run_training.py`; use `key=value` for an existing field. Quote lists and tokens
that resemble numbers, for example `scenario_filter.scenario_tokens='["001"]'`.
Do not transplant an interactive notebook launcher such as `ddp_spawn` into a
non-interactive run without explicitly verifying that launcher.

## Feature, target, and shape failures

### `Objective target ... is not in model computed targets`

Compare:

```python
model.get_list_of_computed_target()
objective.get_list_of_required_target_types()
metric.get_list_of_required_target_types()
```

The ordinary ego trajectory key is exactly `trajectory`. `AgentsImitationObjective`
and agent metrics require `agents_trajectory`, which the bundled ego target
builder does not provide. Changing a YAML label does not rename a builder's
`get_feature_unique_name()` result.

### Forward or loss shape error

Check in this order:

- future output dimension is `num_poses * 3` for `[x, y, heading]`;
- target and model use the same future `num_poses` and `time_horizon`;
- past history matches the first model layer's expected dimensions;
- raster `num_input_channels` equals the raster model input stem;
- channel-last NumPy raster is converted once to channel-first Torch;
- vector features use `FeatureCollate`, not `default_collate`;
- Urban Driver `feature_dimension`, `total_max_points`, `max_agents`,
  `max_elements`, `max_points`, feature labels, and selected layers agree.

Inspect one unbatched object before the loader and one batched object after
collation. `Trajectory` accepts `[num_poses, 3]` or `[batch, num_poses, 3]`.
`Agents`, `GenericAgents`, `VectorMap`, and `VectorSetMap` intentionally contain
variable-size lists/dictionaries.

### Invalid or empty features

Check `.is_valid`, map coverage, query radius, agent history, and the scenario's
available future horizon. Empty agents may be valid for vector paths, but an
invalid map/raster/trajectory or short future target must not be silently cached.
The preprocessor reports the scenario token and log name; preserve that context
in the failure report.

## Cache and data failures

### Empty cache or no scenarios

A cache-only run must contain every required feature and target key for every
selected scenario. Verify the model selected for training is the same model used
to create the cache. A stale cache can contain files with matching names but
incompatible constructor parameters; use a new cache root or force recomputation
with real dataset scenarios.

`cache.use_cache_without_dataset=true` cannot recover a missing entry. Turn it
off, point the scenario builder at a valid dataset, and regenerate. If filtering
by scenario type, preserve `<log>/<scenario-type>/<token>` cache nesting; a
cache without the scenario-type component cannot support that filter.

`cache.cleanup_cache=true` deletes the configured local cache root during config
update. Never enable it during diagnosis unless deletion is intentional. S3
caching is not a verified minimal path: credentials, endpoint access, metadata,
and remote performance remain external assumptions.

Missing DBs, maps, scenario types, or dataset roots belong to the
`data-and-maps` route. Do not solve a data-root failure by changing model code or
downloading data implicitly.

## CPU/CUDA, precision, and numerical failures

The package's historical requirement set uses Python 3.9, Torch 1.9.0+cu111 on
Linux, torchvision 0.10.0, and PyTorch Lightning 1.3.8. Newer Torch/TorchVision,
Hydra, Lightning, or TIMM combinations can fail at import/construction time;
upgrade the compatible set together rather than one Torch component in
isolation. A CUDA import/smoke check was available for this source snapshot, but this
does not establish a portable hardware guarantee.

The config update path checks both the requested GPU flag and CUDA availability.
If either is false, it sets CPU-compatible trainer values and precision 32. The
default CUDA path requests all visible GPUs, DDP, and precision 16. FP16 is
optional and may be numerically unstable. For NaN, Inf, exploding loss, or an
invalid gradient:

1. set `lightning.trainer.params.precision=32` and keep `terminate_on_nan=true`;
2. disable nonessential augmentation and use a fixed small scope;
3. check `torch.isfinite` for input features, targets, model output, objective
   terms, and gradients at the first failing step;
4. inspect coordinate transforms, target horizon, masks, empty reductions, and
   zero-availability map entries;
5. lower the learning rate or clip gradients only after data/loss finiteness is
   established;
6. restore augmentation and FP16 one at a time.

Some global-to-local geometry operations intentionally use float64 before model
input conversion. Do not blanket-cast those intermediate operations to FP16.

## Workers, DDP, and resume

Reproduce worker crashes/hangs with `worker=sequential` and
`num_workers=0`. Then try `single_machine_thread_pool` and explicitly vary its
process-pool option. Only after the local path works should Ray or DDP return.
A distributed run requires every process to see the same dataset/cache and
non-empty partitions; it can also change optimizer/LR scaling, so record world
size and resolved config before comparing runs.

Checkpoint resume fails if `resume_training=true` but no latest checkpoint exists.
Disable resume for a fresh experiment or provide the expected output/checkpoint;
checkpoint loading belongs after a compatible model/target shape is established.

## Expensive and unverified paths

Full training and full cache generation require real dataset/map storage and
substantial compute. TIMM pretrained weights may require network/cache access.
Remote workers, S3, Docker, downloads, notebook launchers, and benchmark
reproduction are not part of the verified minimal path. A successful YAML parse
or model construction does not prove those paths.
