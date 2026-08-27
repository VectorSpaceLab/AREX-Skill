---
name: training
description: "Routes Chainer define-by-run, dataset, trainer, serializer, and
  single-node example workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Training

Use this sub-skill for ordinary Chainer model-building and training tasks.
It covers define-by-run code, datasets, iterators, trainers, extensions, serializers, and single-node CPU or GPU execution.

## Typical requests

- "How do I define a model with `Link`, `Chain`, or `ChainList`?"
- "How do I train a classifier or language model?"
- "How do I save and resume a `Trainer`?"
- "How do I use `SerialIterator`, `Evaluator`, or `LogReport`?"
- "How do I move the model or data to GPU?"
- "How do I use the MNIST, CIFAR, PTB, or serialization examples?"

## Read these first

- `references/workflows.md` for the training flow.
- `references/api-reference.md` for the key classes and exact signatures.
- `references/examples.md` for the example-family map.
- `references/troubleshooting.md` for training, serialization, and device issues.

## Use these scripts

- `../../scripts/training_smoke.py` for a tiny end-to-end training loop.
- `../../scripts/serialization_smoke.py` for NPZ and HDF5 save/load checks.
- `../../scripts/runtime_probe.py` when the environment might not import cleanly.

## Include here

- Define-by-run model construction with `Variable`, `Function`, `Link`, `Chain`, `ChainList`, and `Sequential`.
- Dataset and iterator workflows, including `DatasetMixin`, `TupleDataset`, `SerialIterator`, and minibatch conversion.
- `Trainer`, `StandardUpdater`, `ParallelUpdater`, triggers, and built-in extensions.
- Snapshot and persistence workflows with `save_npz`, `load_npz`, and HDF5 when available.
- CPU and GPU single-node workflows, including `to_gpu`, `to_cpu`, `get_device`, and `using_device`.
- Static-graph optimization examples when the model is a repeated schedule.

## Route elsewhere

- ONNX or Caffe conversion -> `../export/`
- ChainerMN / MPI / multi-node training -> `../distributed/`
- ChainerX build or device behavior -> `../chainerx/`
- Repository build and test questions -> root install and troubleshooting references

## Quick mental model

A typical single-node workflow is:

1. Build the model with `Link` or `Chain`.
2. Prepare a dataset and iterator.
3. Wrap the model with an optimizer.
4. Create an updater and trainer.
5. Add evaluators, reporters, and snapshot extensions.
6. Save and load state with serializers.

If the user asks for a runnable check, prefer the bundled smoke scripts over the original repo examples.
