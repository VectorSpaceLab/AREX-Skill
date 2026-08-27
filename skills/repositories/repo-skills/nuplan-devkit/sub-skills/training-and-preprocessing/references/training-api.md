# Training API and preprocessing data flow

This reference is the runtime contract for the nuPlan-devkit 1.2.2 training
stack. It names package APIs and builder keys rather than relying on a particular
checkout layout. It describes construction and bounded smoke tests; it does not
claim a full-dataset or benchmark run.

## Execution data flow

The training path is:

```text
scenario builder + scenario filter
  -> selected AbstractScenario objects
  -> splitter (train / validation / test)
  -> ScenarioDataset
  -> FeaturePreprocessor
       -> feature builders and target builders
       -> optional local/S3 cache reads and writes
  -> FeatureCollate
  -> DataModule device transfer
  -> TorchModuleWrapper.forward(features)
  -> objectives and training metrics against targets
  -> PyTorch Lightning Trainer
```

`ScenarioDataset.__getitem__` produces `(features, targets, scenarios)`. Feature
and target dictionaries are keyed by `get_feature_unique_name()`. The normal
trajectory target key is `trajectory`. `FeatureCollate`, not Torch's ordinary
`default_collate`, is required for variable-size `Agents`, `GenericAgents`,
`VectorMap`, and `VectorSetMap` values.

## Verified builder and orchestration APIs

The following names are the package's training construction boundaries:

| Import path | Builder/function | Contract |
| --- | --- | --- |
| `nuplan.planning.script.builders.model_builder` | `build_torch_module_wrapper(cfg.model)` | Hydra-instantiates `cfg.model`, then checks that the result is a `TorchModuleWrapper`. |
| `nuplan.planning.script.builders.scenario_builder` | `build_scenarios(cfg, worker, model)` | Selects dataset-backed or cache-backed scenarios using the model's builder names. |
| `nuplan.planning.script.builders.training_builder` | `build_lightning_datamodule(cfg, worker, model)` | Uses the model's feature/target builders, splitter, scenario selection, cache, augmentors, and loader parameters to create `DataModule`. |
| `nuplan.planning.script.builders.training_builder` | `build_lightning_module(cfg, torch_module_wrapper)` | Builds configured objectives and metrics and checks their target names against the model's targets. |
| `nuplan.planning.script.builders.training_builder` | `build_trainer(cfg)` | Builds callbacks, logger, optional checkpoint resume, and `pytorch_lightning.Trainer`. |
| `nuplan.planning.training.experiments.training` | `build_training_engine(cfg, worker)` | Returns a `TrainingEngine` containing trainer, Lightning model, and datamodule. |
| `nuplan.planning.training.experiments.caching` | `cache_data(cfg, worker)` | Computes and stores features/targets; it does not train a model. |
| `nuplan.planning.script.run_training` | `main(cfg)` | Dispatches `py_func=train`, `test`, or `cache`; another value is invalid. |

`run_training.py` first seeds, logs, calls `update_config_for_training`, creates
the experiment folder, and builds the worker. `update_config_for_training`
creates a local cache directory when configured, resolves interpolations, and
changes the trainer to CPU/precision 32 when either the config disables GPU or
CUDA is unavailable.

## Model wrapper contract

A model subclasses
`nuplan.planning.training.modeling.torch_module_wrapper.TorchModuleWrapper` and
receives:

```python
TorchModuleWrapper(
    future_trajectory_sampling,
    feature_builders,
    target_builders,
)
```

It must implement `forward(features)` and return a target dictionary. The
wrapper methods are the source of truth for preprocessing:

```python
model.get_list_of_required_feature()
model.get_list_of_computed_target()
```

Do not type feature names independently in a training config. A custom
`AbstractModelFeature` must support `to_feature_tensor()`, `to_device()`,
`deserialize()`, and `unpack()`; use a custom `collate()` when samples are not
rectangular tensors. Deterministic feature/target builders are cacheable. Put
random perturbations in an `AbstractAugmentor`, not in a cached builder.

## Exact builder names and outputs

These are the builder classes and their verified unique dictionary keys:

| Class | Unique key | Feature/target type | Used by |
| --- | --- | --- | --- |
| `nuplan.planning.training.preprocessing.feature_builders.raster_feature_builder.RasterFeatureBuilder` | `raster` | `Raster` | `RasterModel` |
| `nuplan.planning.training.preprocessing.feature_builders.vector_map_feature_builder.VectorMapFeatureBuilder` | `vector_map` | `VectorMap` | `LaneGCN`, `VectorMapSimpleMLP` |
| `nuplan.planning.training.preprocessing.feature_builders.agents_feature_builder.AgentsFeatureBuilder` | `agents` | `Agents` | `LaneGCN`, `VectorMapSimpleMLP` |
| `nuplan.planning.training.preprocessing.feature_builders.vector_set_map_feature_builder.VectorSetMapFeatureBuilder` | `vector_set_map` | `VectorSetMap` | `UrbanDriverOpenLoopModel` |
| `nuplan.planning.training.preprocessing.feature_builders.generic_agents_feature_builder.GenericAgentsFeatureBuilder` | `generic_agents` | `GenericAgents` | `UrbanDriverOpenLoopModel` |
| `nuplan.planning.training.preprocessing.target_builders.ego_trajectory_target_builder.EgoTrajectoryTargetBuilder` | `trajectory` | `Trajectory` | all bundled planning models |

`EgoTrajectoryTargetBuilder` samples
`scenario.get_ego_future_trajectory(iteration=0, num_samples, time_horizon)`,
converts rear-axle poses to the local ego frame, and raises if the requested
number of poses is not available. The feature preprocessor computes every
feature builder and every target builder in order, then returns dictionaries
under exactly these keys.

## DataModule, collation, and loader rules

`build_lightning_datamodule` derives builders from the wrapper, then constructs
`FeaturePreprocessor`, splitter, augmentors, selected scenarios, and
`DataModule`. `DataModule.setup("fit")` requires non-empty train and validation
splits; `setup("test")` creates the test split. Train and validation fractions
must be positive; test fraction may be zero. Because the implementation computes
`int(len(samples) * fraction)` and uses `random.sample`, a tiny fractional value
can select zero examples. Start with an integer-sized scenario limit.

Loader values live under `data_loader.params` (`batch_size`, `num_workers`,
`pin_memory`, and `drop_last`). For the first diagnosis use
`worker=sequential`, `data_loader.params.num_workers=0`, a tiny scenario filter,
and `drop_last=false` if the sample count is smaller than the batch size.
`FeatureCollate` invokes each feature class's `collate` method and also batches
scenario lists. `pin_memory` follows the GPU choice; it does not move custom
feature objects to a device.

Scenario-type weighted sampling is enabled only when
`scenario_type_weights.enable` is true. Unknown scenario types receive weight
`1.0`; when sampling without replacement, all configured weights must be
positive.

## Lightning objectives and metrics

`build_lightning_module` creates `LightningModuleWrapper`, which checks every
objective and metric's `get_list_of_required_target_types()` against the model's
computed target names. The ordinary ego-trajectory objective and metrics require
`trajectory`:

- `nuplan.planning.training.modeling.objectives.imitation_objective.ImitationObjective`
- `nuplan.planning.training.modeling.objectives.trajectory_weight_decay_imitation_objective.TrajectoryWeightDecayImitationObjective`
- `AverageDisplacementError`, `FinalDisplacementError`, `AverageHeadingError`,
  and `FinalHeadingError` from
  `nuplan.planning.training.modeling.metrics.planning_metrics`

`AgentsImitationObjective` and agent metrics require `agents_trajectory`, which
is not supplied by the ordinary ego-only target builder. Do not combine them
with an ego-only model unless a compatible target builder/model is added.
Objectives aggregate by configured `mean`, `sum`, or `max`; metrics are logged
and are not backpropagated. Heading metrics use wrapped angular differences.

## Configuration and safe verification boundary

The low-cost boundary is YAML validation, Hydra composition inspection,
model-builder construction, datamodule setup with a tiny/mock scenario set, one
batch, and a cache round trip. Native package tests cover model construction,
preprocessing features, cache utilities, and dataloader paths. Full training,
full cache generation, real dataset downloads, notebooks, and benchmark claims
are outside this route.

Run the bundled parser before any constructor or dataset operation:

```bash
python skills/disco/nuplan-devkit/sub-skills/training-and-preprocessing/scripts/validate_training_config.py --config config.yaml
```

That parser uses only safe YAML parsing. It does not import Hydra/model classes,
resolve constructors, access a dataset/cache, download weights, or modify the
config.
