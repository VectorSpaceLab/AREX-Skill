---
name: training-and-preprocessing
description: "Train or fine-tune nuPlan planning models, build and cache
  features and targets, choose raster/vector/Urban Driver pipelines, validate
  Hydra training configuration, and debug preprocessing or numerical failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and preprocessing

Use this route for training or fine-tuning a planning model, constructing input
features or expert targets, precomputing a feature cache, selecting one of the
bundled model families, or diagnosing a training/data-pipeline failure. Keep
scenario-database roots, scenario-builder selection, and map/data acquisition
with the `data-and-maps` route. Keep planner execution and simulation scoring
with `simulation-and-evaluation`.

## Route first

1. Identify the model family and its required feature/target names. Use
   [features, models, and configs](references/features-models-and-configs.md).
2. Check that the selected model, objectives, and metrics agree on target names
   and that the future trajectory shape is identical across model and target.
3. Choose a small, deterministic scenario filter and `worker=sequential` for a
   first build or preprocessing diagnosis. Do not start full training while
   validating a configuration.
4. Validate YAML structure and interpolated-looking values without executing
   constructors with `scripts/validate_training_config.py`. The standalone
   document must expose top-level `training`, `model`, `cache`, and `worker`
   sections; validate a materialized Hydra composition rather than an incomplete
   source fragment that only contains `defaults`.
5. Decide between on-demand preprocessing and a cache. A cache is generally
   preferred for repeated training; a cache-only run requires every required
   feature and target for every selected scenario.
6. Run a one-batch dataloader/build smoke test before a long job. Full training,
   notebook execution, and full-dataset caching are expensive and data-dependent.

## Canonical contracts

- `build_torch_module_wrapper(cfg.model)` instantiates and type-checks a
  `TorchModuleWrapper`.
- The wrapper owns `get_list_of_required_feature()` and
  `get_list_of_computed_target()`. The preprocessor uses those lists; do not
  independently invent feature keys in a config.
- `build_lightning_datamodule(cfg, worker, model)` creates a `DataModule` from
  the model's builders, splitter, scenario selection, cache settings, and
  loader parameters.
- `build_lightning_module(cfg, torch_module_wrapper)` instantiates objectives
  and metrics, then checks that every objective/metric target is supplied by
  the model.
- `build_trainer(cfg)` creates the PyTorch Lightning trainer and handles
  callbacks, logging, and optional resume-from-latest-checkpoint behavior.
- The command-line entry point supports `py_func=train`, `test`, or `cache`.
  `cache` computes features/targets; it does not train a model.

Detailed signatures, data flow, and safe smoke-test boundaries are in
[training API](references/training-api.md).

## Safe command patterns

From the project that supplies the selected nuPlan Hydra configuration:

```bash
python skills/disco/nuplan-devkit/sub-skills/training-and-preprocessing/scripts/validate_training_config.py --config path/to/config.yaml
python -m nuplan.planning.script.run_training +training=training_raster_model worker=sequential py_func=cache cache.force_feature_computation=true
python -m nuplan.planning.script.run_training +training=training_raster_model worker=sequential py_func=train lightning.trainer.params.fast_dev_run=true lightning.trainer.params.max_epochs=1
```

The bundled validator is self-contained; the package training module still
requires a materialized config workspace, local data, and a writable output or
cache root. The cache command reads the configured dataset and writes cache
data; use only a tiny scenario selection and an explicit cache path. The train
command is a smoke test, not a performance or benchmark claim. Never enable
cache-only mode until the cache has been populated with the exact model builder
set.

## Model choice in one view

- **RasterModel / `raster_model`**: CNN/TIMM backbone over a four-channel raster
  by default; simplest image baseline, but sensitive to raster geometry and
  optional TIMM/torchvision compatibility.
- **LaneGCN / `vector_model`**: `VectorMap` plus `Agents`, lane graph
  connections, and attention; preserves lane topology and has variable-size
  per-sample structures.
- **VectorMapSimpleMLP / `simple_vector_model`**: compact vector baseline over
  ego, agent, and lane signals; useful for a quick functional smoke test.
- **UrbanDriverOpenLoopModel / `urban_driver_open_loop_model`**:
  `VectorSetMap` plus `GenericAgents`, fixed-size polylines, attention, and
  augmentation; more configuration-sensitive and intended for open-loop
  trajectory prediction.

See the model/config matrix and shape rules in
[features, models, and configs](references/features-models-and-configs.md).

## Failure routing

- Missing data, maps, DB files, scenario types, or cache directories: first
  inspect the selected builder/filter and route data-root details to
  `data-and-maps`; use [troubleshooting](references/troubleshooting.md) for
  cache invariants.
- A key/type/shape mismatch: compare builder unique names, feature classes,
  target classes, and sampling parameters using the API reference.
- NaN, overflow, or unstable gradients: immediately switch trainer precision
  to 32, disable unnecessary augmentation, reduce the smoke-test scope, and
  inspect the first non-finite tensor before considering FP16 again.
- Worker hangs or crashes: reproduce with `worker=sequential`, then try a
  single-machine thread/process pool; do not treat a distributed run as the
  first diagnostic.
- Checkpoint resume or simulation loading: confirm the materialized Hydra
  config and checkpoint shape; planner execution itself belongs to the
  simulation route.

Consult [troubleshooting](references/troubleshooting.md) for recovery order,
known backend limits, and the difficult NaN/shape/cache cases.

## Verified limits

The package's declared historical compatibility point is Python 3.9 with
NumPy 1.23.4, hydra-core 1.1.0rc1, PyTorch 1.9.0+cu111, and PyTorch
Lightning 1.3.8. A CUDA import/smoke check was available for this source
snapshot, but that evidence is not a portable hardware guarantee and does not
prove that the pinned training stack is compatible. CPU mode is supported by
the configuration update path and forces trainer precision 32. The default
config requests CUDA, DDP, and precision 16 when a GPU is available; FP16 is
optional and may be numerically unstable. S3, Docker, downloads, and full
training remain environment- and data-dependent and are not verified by this
route.

## Evidence boundary

This route is distilled from the package's training builders, preprocessing,
models, objectives, metrics, configs, native dataloader/cache tests, FAQ,
baseline notes, and the two training tutorials. Tutorials explain intent and
composition only; they are not a substitute for a smoke test. Do not claim
benchmark reproduction from these instructions.
