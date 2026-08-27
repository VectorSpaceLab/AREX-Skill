# Helpers API Reference

## Purpose

Read this for the helper classes that back the LabML training-loop workflows.

## Device helpers

| Object | Signature | Use |
| --- | --- | --- |
| `DeviceInfo` | `(*, use_cuda: bool, cuda_device: int)` | Resolve the selected device and expose a readable summary. |
| `DeviceConfigs` | `()` | Configurable device selector that falls back to CPU when CUDA is unavailable. |

`DeviceInfo` reports `is_cuda`, `device`, and the selected device name. The
`DeviceConfigs` config class exposes `use_cuda`, `cuda_device`, `device_info`,
and `device`.

## Optimizers

| Object | Signature | Use |
| --- | --- | --- |
| `OptimizerConfigs` | `()` | Configurable optimizer wrapper with `SGD`, `Adam`, and `Noam` choices. |
| `NoamOpt` | `__init__(model_size, learning_rate, warmup, step_factor, optimizer)` | Learning-rate schedule wrapper around an Adam optimizer. |

Important `OptimizerConfigs` fields:
- `learning_rate`
- `momentum`
- `parameters`
- `d_model`
- `betas`
- `eps`
- `step_factor`

## Datasets

| Object | Signature | Use |
| --- | --- | --- |
| `MNISTConfigs` | `(*, _primary: str = None)` | Configurable MNIST dataset and loader bundle. |
| `CIFAR10Configs` | `(*, _primary: str = None)` | Configurable CIFAR-10 dataset and loader bundle. |
| `RemoteDataset` | `(name: str, host: str = "0.0.0.0", port: int = 8000)` | Fetch dataset items from an HTTP dataset server. |
| `DatasetServer` | `()` | Serve torch datasets over HTTP with FastAPI and uvicorn. |

`MNISTConfigs` and `CIFAR10Configs` expose dataset names, transforms, datasets,
loader objects, batch sizes, and shuffle flags.

## Training-loop core

| Object | Signature | Use |
| --- | --- | --- |
| `TrainingLoopIterator` | `__init__(start, total, step)` | Internal iterator used by `TrainingLoop`. |
| `TrainingLoop` | `__init__(*, loop_count, loop_step, is_save_models, log_new_line_interval, log_write_interval, save_models_interval, is_loop_on_interrupt)` | Monitored loop with checkpoint/log cadence. |
| `TrainingLoopConfigs` | `(*, _primary: str = None)` | Configurable wrapper around `TrainingLoop`. |
| `ModeState` | `()` | Mutable mode flags for train/validate/logging state. |
| `Mode` | `__enter__/__exit__` context manager | Apply temporary mode changes. |
| `Trainer` | `__init__(*, name, mode, data_loader, inner_iterations, state_modules, is_track_time, step)` | Drive a data loader while updating state modules. |
| `BatchIndex` | `__init__(total, total_iterations)` | Track batch/epoch progress and interval checks. |
| `TrainValidConfigs` | `(*, _primary: str = None)` | Base class for alternating training and validation. |
| `SimpleTrainValidConfigs` | `(*, _primary: str = None)` | Higher-level supervised-training helper with a model, optimizer, and loss. |
| `hook_model_outputs` | `(mode, model, model_name='model')` | Register forward hooks for activation logging. |

## Metrics and state modules

| Object | Signature | Use |
| --- | --- | --- |
| `StateModule` | base class | Stateful helper module interface. |
| `Metric` | abstract base | Metric interface built on `StateModule`. |
| `Accuracy` | `__call__(output, target)` | Multiclass accuracy with optional `ignore_index`. |
| `AccuracyMovingAvg` | `__init__(ignore_index=-1, queue_size=5)` | Running accuracy indicator. |
| `BinaryAccuracy` | `__call__(output, target)` | Binary accuracy helper. |
| `AccuracyDirect` | `__call__(output, target)` | Direct equality-based accuracy helper. |
| `Collector` | stateful metric helper | Collect arbitrary values by name. |
| `RecallPrecision` | `__call__(output, target)` | Recall/precision metric helper. |

## Module wrappers and seeding

| Object | Signature | Use |
| --- | --- | --- |
| `Module` | `torch.nn.Module` subclass | Lets subclasses implement `__call__` instead of `forward`. |
| `TypedModuleList` | `torch.nn.ModuleList` subclass | Typed wrapper around `ModuleList`. |
| `SeedConfigs` | `(*, _primary: str = None)` | Configurable seed helper with a `set` action. |

## Remote dataset helpers

`labml_helpers.datasets.remote` provides two complementary classes:

- `DatasetServer`: add one or more torch datasets with `add_dataset(name,
  dataset)` and start the FastAPI server with `start(host='0.0.0.0', port=8000)`.
- `RemoteDataset`: create a client with `RemoteDataset(name, host='0.0.0.0',
  port=8000)` and use it like a torch dataset.

The transport uses HTTP and pickle serialization. It is convenient for local or
LAN-only setups, but it is not a security-hardened public dataset service.

## When to cross-check the source

Use the smoke scripts and source inspection if you need exact overload behavior,
model-state semantics, or helper defaults that are not listed here.
