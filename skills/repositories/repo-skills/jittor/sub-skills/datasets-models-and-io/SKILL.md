---
name: datasets-models-and-io
description: "Route Jittor data loading, transforms, built-in datasets, model
  zoo constructors, pretrained weights, and checkpoint I/O."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# datasets-models-and-io

Use this sub-skill when a task needs to build or debug a Jittor input pipeline, choose a built-in dataset, apply image transforms, instantiate a model-zoo backbone, avoid accidental downloads, or move checkpoints between Jittor and PyTorch-style files.

Do not use this sub-skill for optimizer details, full training-loop design, low-level `Var`/autograd semantics, backend installation, performance flags, custom operators, or converter service operation. Route those topics to the sibling sub-skills that own them.

## Read or run

- Read [references/data-and-transform-reference.md](references/data-and-transform-reference.md) when selecting `Dataset`, `DataLoader`, `ImageFolder`, `TensorDataset`, MNIST, CIFAR, VOC, or `jittor.transform` workflows.
- Read [references/model-zoo-and-checkpoints.md](references/model-zoo-and-checkpoints.md) when constructing `jittor.models` backbones, deciding whether `pretrained=True` is safe, saving/loading Jittor state, or attempting PyTorch checkpoint interop.
- Read [references/troubleshooting.md](references/troubleshooting.md) when data downloads fail, a cache or checkpoint appears corrupt, workers hang, transforms change layout unexpectedly, pretrained weights try to use the network, or optional PyTorch is unavailable.
- Run [scripts/data_model_smoke.py](scripts/data_model_smoke.py) for a no-download synthetic data/transform/TensorDataset plus `resnet18(pretrained=False)` shape smoke.

## Safe default decisions

1. For smoke tests and CI, prefer synthetic arrays or `TensorDataset`; set all built-in dataset downloads and model pretrained flags off unless data or weights are already present.
2. The bundled smoke script clears CUDA auto-detection before importing Jittor so it stays usable on hosts where a mismatched `nvcc` is visible.
3. Keep image transforms in a predictable order: PIL-only spatial/color transforms first, then conversion/normalization to CHW arrays, then batching.
4. Treat Jittor model-zoo constructors as NCHW image classifiers by default; use `pretrained=False` unless the task explicitly permits a network download.
5. For checkpoint loading, validate key names and shapes before trusting a load: Jittor logs skipped or mismatched parameters and may not raise an exception.
