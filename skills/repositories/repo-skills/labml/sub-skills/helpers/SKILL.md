---
name: helpers
description: "Routes LabML helper training loops, metrics, device/optimizer
  configs, datasets, and remote dataset workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Helpers

Use this subskill for `labml_helpers`: configurable training loops, datasets,
metrics, device selection, optimizer selection, model wrappers, and the remote
dataset client/server pair.

## Use this when

- The task mentions `labml_helpers`, `DeviceConfigs`, `OptimizerConfigs`,
  `TrainingLoopConfigs`, `TrainValidConfigs`, `SimpleTrainValidConfigs`,
  `MNISTConfigs`, `CIFAR10Configs`, `Accuracy`, `Collector`, `RecallPrecision`,
  `SeedConfigs`, or `Module`.
- The user wants a reusable supervised-training skeleton, a metric module, or a
  device/optimizer config wrapper.
- The user wants to serve a dataset over HTTP with `DatasetServer` or consume it
  with `RemoteDataset`.

## Boundaries

Include:
- Training-loop abstractions and config classes.
- Metric modules and stateful helper patterns.
- Device and optimizer configs.
- Dataset helpers, including the remote dataset server/client pair.
- Small supervised-learning recipes that stay within the helper package.

Exclude or route elsewhere:
- Client-side logging and monitoring helpers → `tracking`.
- SSH, rsync, or remote job orchestration → `remote`.
- FastAPI app backend and monitoring UI routes → `server`.

## Read next

- `references/api-reference.md` for the verified helper classes and signatures.
- `references/workflows.md` for small training-loop recipes and the remote
  dataset pattern.
- `references/troubleshooting.md` for torch, dataset, device, and remote-dataset
  failures.
- `scripts/helpers_smoke.py` for a safe synthetic training check.
- `scripts/remote_dataset_smoke.py` for a local loopback check of the dataset
  server/client pair.

## Typical routes

### Build a reusable supervised trainer
Choose this route for `SimpleTrainValidConfigs`, `BatchIndex`, `Trainer`, or
metric state modules.

### Choose a device or optimizer
Choose this route for `DeviceConfigs`, `DeviceInfo`, `OptimizerConfigs`, or
`NoamOpt`.

### Use packaged datasets
Choose this route for `MNISTConfigs`, `CIFAR10Configs`, or helpers that build
PyTorch `DataLoader` objects.

### Share a dataset remotely
Choose this route for `DatasetServer`, `RemoteDataset`, and the FastAPI/uvicorn
loopback pattern.
