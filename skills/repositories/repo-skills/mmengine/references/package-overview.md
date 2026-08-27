# MMEngine Package Overview

MMEngine is the foundational OpenMMLab engine package for PyTorch workflows. It provides reusable building blocks for config-driven object construction, training loops, hooks, optimizers, datasets, model/evaluator contracts, logging, visualization, file IO, distributed helpers, and runtime utilities.

## Install and Import Surface

Typical public installation uses one of these forms:

```bash
pip install -U openmim
mim install mmengine
```

or, for ordinary pip environments:

```bash
pip install mmengine
```

A minimal import check is:

```bash
python -c "import mmengine; print(mmengine.__version__)"
python -c "from mmengine.config import Config; from mmengine.registry import Registry; print(Config, Registry)"
```

MMEngine exposes a broad package import surface rather than console scripts. Common top-level API families are:

| API family | Typical objects |
| --- | --- |
| Configuration and registry | `Config`, `ConfigDict`, `Registry`, `DefaultScope`, `build_from_cfg`, root registries such as `MODELS`, `DATASETS`, `HOOKS` |
| Runner and training | `Runner`, `FlexibleRunner`, loops, checkpoint/resume helpers, hook priorities, randomness helpers |
| Hooks and optimization | `Hook`, `CheckpointHook`, `LoggerHook`, `ParamSchedulerHook`, `EarlyStoppingHook`, `OptimWrapper`, `AmpOptimWrapper`, param schedulers |
| Data and IO | `BaseDataset`, `Compose`, `DefaultSampler`, `pseudo_collate`, `default_collate`, `BaseDataElement`, `InstanceData`, `PixelData`, `LabelData`, `load`, `dump`, file backends |
| Model and evaluation | `BaseModel`, `BaseModule`, data preprocessors, `BaseMetric`, `Evaluator`, `DumpResults`, `BaseInferencer`, `BaseTTAModel` |
| Runtime utilities | `MMLogger`, `MessageHub`, `Visualizer`, visual backends, distributed helpers, device/environment utilities, timers, progress helpers, testing utilities |

## Dependency Model

The core runtime dependencies include Python packages for configuration, arrays, YAML, rich terminal output, formatting, and plotting. PyTorch is required for most runner, model, evaluator, TTA, and analysis workflows. OpenCV may be needed by visualization hooks and image utilities. Optional service integrations and large-model strategies add additional dependencies and often credentials, launchers, or GPU hardware.

Safe default path:

1. Prove `import mmengine` and the needed submodules.
2. Prove PyTorch import for runner/model work.
3. Add OpenCV headless if importing runner/hooks reaches visualization image helpers.
4. Add optional tracking or strategy packages only for workflows that explicitly require them.

## How Sub-Skills Fit Together

A complete MMEngine project usually crosses several sub-skills:

1. `configuration-and-registry` builds the config and registry layer.
2. `data-structures-and-io` defines records, transforms, samples, and file IO.
3. `models-metrics-and-inference` defines model and evaluator contracts.
4. `runner-and-training` orchestrates loops, hooks, optimization, checkpointing, and launch.
5. `runtime-utilities-and-visualization` manages logs, visual outputs, environment checks, distributed helpers, and optional backends.

When debugging, identify the first layer that fails instead of changing all layers at once. For example, a `KeyError` from `build_from_cfg` belongs to config/registry, a `TypeError` in `collate` belongs to data, a missing `loss` key belongs to model contracts, and a missing checkpoint best metric belongs to runner/evaluator integration.
