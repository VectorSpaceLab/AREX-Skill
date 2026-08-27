# Features, models, targets, and Hydra configuration

This matrix is distilled from the nuPlan-devkit 1.2.2 model configs and model/
feature-builder implementations. It is a compatibility guide, not a benchmark
claim.

## Shared trajectory contract

All four bundled planning models predict `trajectory`, produced by
`nuplan.planning.training.preprocessing.target_builders.ego_trajectory_target_builder.EgoTrajectoryTargetBuilder`.
Each state is `[x, y, heading]` in meters, meters, and radians, relative to the
current ego rear axle. For a batched target the shape is
`[batch, num_poses, 3]`. The model output, target builder, objectives, and
metrics must agree on `num_poses` and `time_horizon`.

The bundled configs use 16 future poses over 8.0 seconds and therefore 48 output
features (`16 * 3`). If a custom model changes either sampling value, update the
model's output dimension and target-builder sampling together. The target
builder rejects scenarios that cannot provide all requested future poses.

## Model-family matrix

| Experiment/config | Exact model class | Required feature keys | Target | Main risks |
| --- | --- | --- | --- | --- |
| `training_raster_model` / `raster_model` | `nuplan.planning.training.modeling.models.raster_model.RasterModel` | `raster` | `trajectory` | channel count/order, raster geometry, optional TIMM weights |
| `training_vector_model` / `vector_model` | `nuplan.planning.training.modeling.models.lanegcn_model.LaneGCN` | `vector_map`, `agents` | `trajectory` | variable lane/agent counts, graph hops, history dimensions |
| `training_simple_vector_model` / `simple_vector_model` | `nuplan.planning.training.modeling.models.simple_vector_map_model.VectorMapSimpleMLP` | `vector_map`, `agents` | `trajectory` | vector radius/history and 48-output agreement |
| `training_urban_driver_open_loop_model` / `urban_driver_open_loop_model` | `nuplan.planning.training.modeling.models.urban_driver_open_loop_model.UrbanDriverOpenLoopModel` | `vector_set_map`, `generic_agents` | `trajectory` | fixed padding, feature dimensions, map/agent type configuration |

The model builder's exact entry point is
`nuplan.planning.script.builders.model_builder.build_torch_module_wrapper`.
It uses Hydra `instantiate(cfg.model)` and checks the resulting object is a
`TorchModuleWrapper`. Missing or incompatible `_target_` values fail before
scenario construction.

## Raster pipeline

`RasterFeatureBuilder` has the exact import path
`nuplan.planning.training.preprocessing.feature_builders.raster_feature_builder.RasterFeatureBuilder`
and returns `Raster` under `raster`. Its constructor requires:

- `map_features` (layer-to-encoding mapping)
- `num_input_channels`
- `target_width`, `target_height`, `target_pixel_size`
- `ego_width`, `ego_front_length`, `ego_rear_length`
- `ego_longitudinal_offset`, `baseline_path_thickness`

The builder emits channel-last NumPy data `[H, W, C]`; `Raster.to_feature_tensor()`
converts it to channel-first Torch data `[C, H, W]`. The bundled raster config
uses 224x224 at 0.5 m/pixel, four input channels, map features `LANE`,
`INTERSECTION`, `STOP_LINE`, and `CROSSWALK`, and a `resnet50` TIMM backbone.
The model creates its output layer from
`future_trajectory_sampling.num_poses * num_features_per_pose`; it does not
accept an arbitrary output dimension safely.

`pretrained: true` can require an external TIMM weight acquisition. For an
offline smoke test, use an installed backbone and disable weight acquisition if
the selected model/config supports it. A changed raster channel count must be
checked against the model's first convolution; do not manually transpose a
raster that is already a Torch feature tensor.

## Vector map and agents pipeline

`VectorMapFeatureBuilder` returns `VectorMap` under `vector_map`. It extracts
lane segment coordinates, groupings, multi-scale integer connections, on-route
status, and traffic-light encoding around the ego rear axle. LaneGCN's config
uses radius 50 m and connection scales `[1, 2, 3, 4]`; the simple baseline uses
radius 20 m and one-hop connections by default.

`AgentsFeatureBuilder` returns `Agents` under `agents`. Its configured sampling
contains past frames plus the current frame. Ego states are `[num_frames, 3]`;
agent states are `[num_frames, num_agents, 8]` with pose, velocity, yaw rate, and
size. The supported builder object types in this version are vehicle and
pedestrian. Empty agent sets are represented explicitly, but an invalid feature
still must not be silently cached or trained.

Both feature types have variable-size samples and require `FeatureCollate`; do
not use ordinary `default_collate`. Verify the history length expected by the
model's first layers against `past_trajectory_sampling`.

## Urban Driver pipeline

`VectorSetMapFeatureBuilder` returns `VectorSetMap` under `vector_set_map`. Its
constructor requires `map_features`, per-layer `max_elements`, per-layer
`max_points`, `radius`, and `interpolation_method`. Every selected layer must
have both max dictionaries populated. It produces fixed-size polylines and
availability masks.

`GenericAgentsFeatureBuilder` returns `GenericAgents` under `generic_agents`.
Its `agent_features` list accepts tracked-object enum names other than `EGO`,
for example `VEHICLE`, `BICYCLE`, and `PEDESTRIAN`. Ego data has seven fields;
each selected agent type has eight fields and variable agent count.

`UrbanDriverOpenLoopModel` additionally requires internally consistent
`feature_dimension`, `total_max_points`, `max_agents`, map-layer limits, agent
feature list, and type labels. The bundled config uses feature labels `EGO`,
`VEHICLE`, `BICYCLE`, `PEDESTRIAN`, `LANE`, `STOP_LINE`, `CROSSWALK`,
`LEFT_BOUNDARY`, `RIGHT_BOUNDARY`, and `ROUTE_LANES`; it selects `VEHICLE` agents
and six map layers. `disable_map` and `disable_agents` alter forward behavior,
but are not a reason to omit builder/config keys without checking the model.

## Targets, objectives, and metrics

The exact target builder is
`nuplan.planning.training.preprocessing.target_builders.ego_trajectory_target_builder.EgoTrajectoryTargetBuilder`.
Its unique key is `trajectory`. Standard objectives are:

```text
nuplan.planning.training.modeling.objectives.imitation_objective.ImitationObjective
nuplan.planning.training.modeling.objectives.trajectory_weight_decay_imitation_objective.TrajectoryWeightDecayImitationObjective
```

Both require `trajectory`; the first combines XY MSE with heading L1, while the
second applies exponentially time-weighted trajectory L1. `AgentsImitationObjective`
requires `agents_trajectory` instead. Standard planning metrics are configured
as `avg_displacement_error`, `avg_heading_error`, `final_displacement_error`,
and `final_heading_error`; all require `trajectory`. A target-name mismatch is a
builder/model contract error, not a YAML spelling problem.

## Hydra composition and command semantics

The base config group is `default_training`. It intentionally leaves model,
splitter, objective, metric, aggregate mode, and `py_func` unresolved until an
experiment fragment or overrides supply them. The coherent fragments are:

```text
+training=training_raster_model
+training=training_simple_vector_model
+training=training_vector_model
+training=training_urban_driver_open_loop_model
```

The installed package entry point is the module
`nuplan.planning.script.run_training`. Its supported operations are:

- `py_func=train`: build the training engine and call `trainer.fit`.
- `py_func=test`: build the engine and call `trainer.test`.
- `py_func=cache`: compute features/targets and write cache metadata; it does
  not train.

A safe first command is a composed run with `worker=sequential`, a tiny
scenario filter, `data_loader.params.num_workers=0`, and trainer precision 32.
Use `+group=value` when adding a config group as in the experiment fragments;
use `key=value` for an existing key. Quote list overrides and tokens that look
numeric. The resolved Hydra config saved in the experiment output is the
authoritative record, not an unresolved source fragment.

Example syntax (dataset/cache work still occurs):

```bash
python -m nuplan.planning.script.run_training \
  +training=training_raster_model worker=sequential \
  data_loader.params.num_workers=0 \
  lightning.trainer.params.precision=32 \
  lightning.trainer.params.fast_dev_run=true \
  lightning.trainer.params.max_epochs=1
```

This module invocation still needs a project-provided, materialized Hydra
training configuration and local dataset/cache roots. Do not treat
`fast_dev_run` as a benchmark. Restrict the scenario filter and cache path
before running it.

## Cache identity and assumptions

`FeaturePreprocessor` uses the wrapper's exact builder names. A conceptual local
entry is:

```text
<cache-root>/<log-name>/<scenario-type>/<scenario-token>/<unique-name>.gz
```

The cache key contains log, scenario type, token, and builder unique name; it
does not encode every constructor parameter. Changing raster geometry, map
radius, interpolation, past history, selected layers, feature list, or target
sampling therefore requires a new cache root or forced recomputation.

`cache.force_feature_computation=true` recomputes and overwrites local entries
when a dataset scenario is available. `cache.use_cache_without_dataset=true`
uses `CachedScenario` and cannot recompute a missing file; every model feature
and target must already exist. Cache-only discovery requires the complete set of
builder keys and preserves scenario-type directories when filtering by type.
Cache cleanup is destructive. S3 cache support is present but credentials,
network access, and remote throughput are not verified here.

## Precision and backend limits

The package requirement set pins an older compatibility point: Python 3.9,
PyTorch 1.9.0 (+cu111 on Linux), torchvision 0.10.0, PyTorch Lightning 1.3.8,
and torchmetrics 0.7.2. A CUDA import/smoke check was available for this
source snapshot, but that is evidence of one prepared environment, not a
portable hardware requirement. CUDA is optional for this route.

`update_config_for_training` forces trainer precision 32 and CPU-compatible
trainer settings when GPU use is disabled or `torch.cuda.is_available()` is
false. The default GPU config requests all visible GPUs, DDP, and precision 16.
FP16 is optional and can produce NaN/Inf or unstable gradients; begin with
FP32, inspect the first non-finite feature/target/output/loss/gradient, and only
re-enable FP16 after the data path is finite. Geometry preprocessing may use
float64 intentionally before producing model-ready data; do not blanket-cast
those operations to FP16.

A generic prepared environment may not contain the exact old Hydra, Lightning,
or TIMM pins. A parser-only verification therefore does not prove model
construction or CUDA training. Record dependency/backend availability before
claiming a native model or dataloader smoke test.
