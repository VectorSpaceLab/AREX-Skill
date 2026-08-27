---
name: graph-data
description: "Guides Spektral graph containers, datasets, transforms, data
  modes, and loader workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Spektral Graph Data

Use this sub-skill when a task is about graph representation, dataset construction, built-in datasets, transforms, data modes, loaders, batching, or data-shape errors in Spektral.

## Read first

- `references/api-reference.md` for `Graph`, `Dataset`, loader, transform, and data utility signatures.
- `references/workflows.md` for custom datasets, loader selection, transforms, and safe in-memory examples.
- `references/dataset-catalog.md` for built-in datasets and cache/download behavior.
- `references/troubleshooting.md` for shape, mode, label, sparse/dense, and dataset-cache failures.
- `scripts/smoke_data_modes.py` for a no-download sanity check of all four data modes and common transforms.

## Core workflow

1. Represent each graph as `Graph(x=None, a=None, e=None, y=None, **kwargs)`.
2. Group graphs in a `Dataset` subclass whose `read()` method returns a list of `Graph` objects.
3. Choose a data mode from the task shape:
   - **single**: one graph, often node-level learning.
   - **disjoint**: many variable-size graphs as one sparse block-diagonal graph.
   - **batch**: many graphs zero-padded into dense tensors.
   - **mixed**: one shared adjacency matrix with many node/edge signals.
4. Pick the matching loader and confirm the emitted tuple before building the Keras model.
5. Apply transforms to mutate graphs before loading, especially `GCNFilter` or `LayerPreprocess` for layer-specific adjacency preprocessing.
6. Hand model/layer architecture questions to `../gnn-models/SKILL.md`.

## Loader selection cheat sheet

| Data shape | Loader | Output idea | Use when |
| --- | --- | --- | --- |
| One graph | `SingleLoader` | `(x, a[, e])[, y[, sample_weights]]` | Single network, citation graph, node labels on one graph |
| Many variable-size graphs | `DisjointLoader` | `(x, a[, e], i), y` | Graph classification/regression with sparse adjacency and global pooling |
| Many graphs padded to dense tensors | `BatchLoader` | `(x, a[, e]), y` | Dense pooling such as MinCut/DiffPool, or fixed-size batch processing |
| Pre-padded dense data | `PackedBatchLoader` | Same as `BatchLoader` | Same graph sizes or enough memory to pre-pack all graphs |
| Shared graph support, many signals | `MixedLoader` | `(x, a[, e]), y` | Graph signal classification, e.g. MNIST on a grid graph |

## Common decisions

- Prefer sparse adjacency (`scipy.sparse`) for graph containers unless a batch-mode layer requires dense tensors.
- Keep sparse edge attributes in row-major order matching nonzero adjacency entries.
- For graph-level tasks with variable-size graphs, start with `DisjointLoader` and global pooling.
- For dense pooling, use `BatchLoader(mask=True)` and then `GraphMasking` in the model route.
- Built-in datasets may download data; avoid them for tiny smoke tests unless a cache already exists.

## Validation steps

Run this sub-skill's script from the generated skill tree after installing Spektral:

```bash
python sub-skills/graph-data/scripts/smoke_data_modes.py
```

Expected signal: loader shapes for single, disjoint, batch, and mixed modes, transform shape updates, and final `smoke_ok`.

## Route away when

- The user asks how to choose or implement convolution or pooling layers: use `../gnn-models/SKILL.md`.
- The user asks generic TensorFlow/Keras training-loop questions without Spektral data structures: use TensorFlow/Keras guidance first.
- The user asks for PyG or DGL data objects: do not map those APIs to Spektral names without an explicit migration task.
